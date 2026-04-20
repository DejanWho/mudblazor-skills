using Amazon.CDK;
using Amazon.CDK.AWS.CertificateManager;
using Amazon.CDK.AWS.EC2;
using Amazon.CDK.AWS.ECS;
using Amazon.CDK.AWS.ElasticLoadBalancingV2;
using Amazon.CDK.AWS.IAM;
using Amazon.CDK.AWS.Logs;
using Constructs;

namespace BedrockChat;

public class BedrockChatStack : Stack
{
    public BedrockChatStack(Construct scope, string id, IStackProps props) : base(scope, id, props)
    {
        var environmentName = this.Node.TryGetContext("environment") as string ?? "dev";
        var vpcCidr = this.Node.TryGetContext("vpc-cidr") as string ?? "10.30.0.0/16";
        var sonnetModelId = this.Node.TryGetContext("claude-sonnet-model-id") as string
            ?? "anthropic.claude-3-5-sonnet-20241022-v2:0";
        var haikuModelId = this.Node.TryGetContext("claude-haiku-model-id") as string
            ?? "anthropic.claude-3-haiku-20240307-v1:0";

        // ---- Networking ----
        var vpc = new Vpc(this, "Vpc", new VpcProps
        {
            IpAddresses = IpAddresses.Cidr(vpcCidr),
            MaxAzs = 3,
            NatGateways = 3,
            SubnetConfiguration = new[]
            {
                new SubnetConfiguration { Name = "public",  SubnetType = SubnetType.PUBLIC,               CidrMask = 24 },
                new SubnetConfiguration { Name = "private", SubnetType = SubnetType.PRIVATE_WITH_EGRESS,  CidrMask = 24 }
            }
        });

        // Security group guarding the Bedrock interface endpoint
        var bedrockEndpointSg = new SecurityGroup(this, "BedrockEndpointSg", new SecurityGroupProps
        {
            Vpc = vpc,
            Description = "Allow Fargate tasks to reach the Bedrock runtime interface endpoint",
            AllowAllOutbound = false
        });

        // Private VPC endpoint so Bedrock traffic doesn't traverse NAT
        vpc.AddInterfaceEndpoint("BedrockRuntimeEndpoint", new InterfaceVpcEndpointOptions
        {
            Service = InterfaceVpcEndpointAwsService.BEDROCK_RUNTIME,
            PrivateDnsEnabled = true,
            SecurityGroups = new[] { bedrockEndpointSg }
        });

        // ---- Compute ----
        var cluster = new Cluster(this, "Cluster", new ClusterProps
        {
            Vpc = vpc,
            ContainerInsightsV2 = ContainerInsights.ENABLED
        });

        var taskLogGroup = new LogGroup(this, "TaskLogGroup", new LogGroupProps
        {
            LogGroupName = $"/ecs/bedrock-chat-{environmentName}",
            Retention = RetentionDays.ONE_MONTH,
            RemovalPolicy = RemovalPolicy.DESTROY
        });

        var executionRole = new Role(this, "TaskExecutionRole", new RoleProps
        {
            AssumedBy = new ServicePrincipal("ecs-tasks.amazonaws.com"),
            ManagedPolicies = new[]
            {
                ManagedPolicy.FromAwsManagedPolicyName("service-role/AmazonECSTaskExecutionRolePolicy")
            }
        });

        var taskRole = new Role(this, "TaskRole", new RoleProps
        {
            AssumedBy = new ServicePrincipal("ecs-tasks.amazonaws.com")
        });

        // Bedrock invocation permissions — Claude 3.5 Sonnet and Claude 3 Haiku
        taskRole.AddToPolicy(new PolicyStatement(new PolicyStatementProps
        {
            Effect = Effect.ALLOW,
            Actions = new[]
            {
                "bedrock:InvokeModel",
                "bedrock:InvokeModelWithResponseStream"
            },
            Resources = new[]
            {
                $"arn:aws:bedrock:{this.Region}::foundation-model/{sonnetModelId}",
                $"arn:aws:bedrock:{this.Region}::foundation-model/{haikuModelId}"
            }
        }));

        var taskDef = new FargateTaskDefinition(this, "TaskDef", new FargateTaskDefinitionProps
        {
            Cpu = 1024,
            MemoryLimitMiB = 2048,
            ExecutionRole = executionRole,
            TaskRole = taskRole
        });

        taskDef.AddContainer("App", new ContainerDefinitionOptions
        {
            Image = ContainerImage.FromRegistry("public.ecr.aws/nginx/nginx:stable"),
            PortMappings = new[] { new PortMapping { ContainerPort = 8080, Protocol = Amazon.CDK.AWS.ECS.Protocol.TCP } },
            Logging = LogDrivers.AwsLogs(new AwsLogDriverProps
            {
                LogGroup = taskLogGroup,
                StreamPrefix = "bedrock-chat"
            }),
            Environment = new System.Collections.Generic.Dictionary<string, string>
            {
                { "ASPNETCORE_ENVIRONMENT", environmentName },
                { "LOG_LEVEL", "Information" },
                { "BEDROCK_SONNET_MODEL_ID", sonnetModelId },
                { "BEDROCK_HAIKU_MODEL_ID", haikuModelId }
            }
        });

        // ---- Load balancing ----
        var albSg = new SecurityGroup(this, "AlbSg", new SecurityGroupProps
        {
            Vpc = vpc,
            Description = "Public ingress for the chat ALB",
            AllowAllOutbound = true
        });
        albSg.AddIngressRule(Peer.AnyIpv4(), Port.Tcp(443), "HTTPS from the world");
        albSg.AddIngressRule(Peer.AnyIpv4(), Port.Tcp(80), "HTTP for redirect");

        var alb = new ApplicationLoadBalancer(this, "Alb", new ApplicationLoadBalancerProps
        {
            Vpc = vpc,
            InternetFacing = true,
            SecurityGroup = albSg
        });

        // Cert is provisioned out-of-stack; CDK imports it
        var certificate = Certificate.FromCertificateArn(
            this, "Certificate",
            "arn:aws:acm:eu-central-1:000000000000:certificate/00000000-0000-0000-0000-000000000000"
        );

        var httpsListener = alb.AddListener("HttpsListener", new BaseApplicationListenerProps
        {
            Port = 443,
            Protocol = ApplicationProtocol.HTTPS,
            Certificates = new[] { certificate },
            SslPolicy = SslPolicy.TLS13_12
        });

        alb.AddListener("HttpListener", new BaseApplicationListenerProps
        {
            Port = 80,
            Protocol = ApplicationProtocol.HTTP,
            DefaultAction = ListenerAction.Redirect(new RedirectOptions
            {
                Port = "443",
                Protocol = "HTTPS",
                Permanent = true
            })
        });

        var service = new FargateService(this, "Service", new FargateServiceProps
        {
            Cluster = cluster,
            TaskDefinition = taskDef,
            DesiredCount = 2,
            AssignPublicIp = false
        });

        // Open the Fargate SG to the ALB on 8080
        service.Connections.AllowFrom(albSg, Port.Tcp(8080), "ALB → tasks");

        // Allow tasks to reach the Bedrock endpoint
        bedrockEndpointSg.AddIngressRule(
            service.Connections.SecurityGroups[0],
            Port.Tcp(443),
            "Fargate → Bedrock endpoint"
        );

        httpsListener.AddTargets("AppTargets", new AddApplicationTargetsProps
        {
            Port = 8080,
            Protocol = ApplicationProtocol.HTTP,
            Targets = new[] { service },
            HealthCheck = new Amazon.CDK.AWS.ElasticLoadBalancingV2.HealthCheck
            {
                Path = "/health",
                HealthyHttpCodes = "200",
                Interval = Duration.Seconds(30),
                Timeout = Duration.Seconds(10),
                HealthyThresholdCount = 2,
                UnhealthyThresholdCount = 3
            }
        });

        // Stack outputs
        new CfnOutput(this, "AlbDnsName", new CfnOutputProps
        {
            Value = alb.LoadBalancerDnsName,
            Description = "Public ALB DNS name"
        });

        new CfnOutput(this, "ServiceArn", new CfnOutputProps
        {
            Value = service.ServiceArn,
            Description = "ECS service ARN"
        });
    }
}
