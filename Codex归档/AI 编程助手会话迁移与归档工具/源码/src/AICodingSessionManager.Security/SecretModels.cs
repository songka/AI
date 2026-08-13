namespace AICodingSessionManager.Security;

/// <summary>Classifies sensitive values recognized by <see cref="SecretScanner"/>.</summary>
public enum SecretKind
{
    /// <summary>An OpenAI API key.</summary>
    OpenAiApiKey,
    /// <summary>An Anthropic API key.</summary>
    AnthropicApiKey,
    /// <summary>A GitHub personal, OAuth, user, server, or refresh token.</summary>
    GitHubToken,
    /// <summary>An AWS access key identifier.</summary>
    AwsAccessKeyId,
    /// <summary>A credential contained in an Authorization header or assignment.</summary>
    AuthorizationHeader,
    /// <summary>A password, token, secret, or API key assigned through an environment-style setting.</summary>
    EnvironmentSecret,
    /// <summary>A PEM-encoded private-key block.</summary>
    PemPrivateKey,
    /// <summary>The user-name segment of a Windows user-profile path.</summary>
    WindowsUserName
}

/// <summary>Describes a sensitive span without retaining its complete value.</summary>
/// <param name="Kind">The detected secret category.</param>
/// <param name="Start">The zero-based character offset in the scanned text.</param>
/// <param name="Length">The number of characters in the sensitive span.</param>
/// <param name="Preview">A bounded, non-reversible hint suitable for diagnostics.</param>
public sealed record SecretFinding(SecretKind Kind, int Start, int Length, string Preview);

/// <summary>Controls which categories the scanner detects.</summary>
public sealed class SecretScannerOptions
{
    /// <summary>Gets or initializes whether provider-specific API keys are detected.</summary>
    public bool DetectProviderKeys { get; init; } = true;
    /// <summary>Gets or initializes whether Authorization credentials are detected.</summary>
    public bool DetectAuthorizationHeaders { get; init; } = true;
    /// <summary>Gets or initializes whether password/token/secret environment assignments are detected.</summary>
    public bool DetectEnvironmentSecrets { get; init; } = true;
    /// <summary>Gets or initializes whether PEM private keys are detected.</summary>
    public bool DetectPemPrivateKeys { get; init; } = true;
    /// <summary>Gets or initializes whether Windows user-profile names are detected.</summary>
    public bool DetectWindowsUserNames { get; init; } = true;
}

/// <summary>Controls how detected spans are replaced.</summary>
public sealed class PrivacyRedactorOptions
{
    /// <summary>Gets or initializes whether a bounded prefix and suffix are retained for non-path secrets.</summary>
    public bool PreserveSecretHints { get; init; }
    /// <summary>Gets or initializes the number of leading characters retained when hints are enabled. Maximum is 8.</summary>
    public int HintPrefixLength { get; init; } = 2;
    /// <summary>Gets or initializes the number of trailing characters retained when hints are enabled. Maximum is 8.</summary>
    public int HintSuffixLength { get; init; } = 2;
}

/// <summary>Contains redacted text and the findings that produced it.</summary>
/// <param name="Text">The privacy-safe text.</param>
/// <param name="Findings">Detected sensitive spans in source order.</param>
public sealed record RedactionResult(string Text, IReadOnlyList<SecretFinding> Findings);
