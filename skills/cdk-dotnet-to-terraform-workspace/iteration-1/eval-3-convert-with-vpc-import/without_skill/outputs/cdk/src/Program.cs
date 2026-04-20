using Amazon.CDK;

namespace BedrockChat;

public static class Program
{
    public static void Main(string[] args)
    {
        var app = new App();

        new BedrockChatStack(app, "BedrockChatStack-dev", new StackProps
        {
            Env = new Environment
            {
                Account = System.Environment.GetEnvironmentVariable("CDK_DEFAULT_ACCOUNT"),
                Region = app.Node.TryGetContext("region") as string ?? "eu-central-1"
            },
            Description = "Bedrock-backed chat API: ALB → Fargate → Bedrock (Anthropic Claude)",
            Tags = new System.Collections.Generic.Dictionary<string, string>
            {
                { "Environment", app.Node.TryGetContext("environment") as string ?? "dev" },
                { "Application", "bedrock-chat" },
                { "ManagedBy", "cdk" }
            }
        });

        app.Synth();
    }
}
