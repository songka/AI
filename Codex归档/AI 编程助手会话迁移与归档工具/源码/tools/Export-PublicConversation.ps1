param(
    [Parameter(Mandatory = $true)]
    [string]$SourceJsonl,

    [Parameter(Mandatory = $true)]
    [string]$OutputDirectory
)

$ErrorActionPreference = 'Stop'
$utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Protect-PublicText([string]$Text) {
    if ([string]::IsNullOrWhiteSpace($Text)) { return $Text }

    $value = $Text
    $value = [regex]::Replace($value, '(?i)C:\\Users\\[^\\\s`"''/]+', '%USERPROFILE%')
    $value = [regex]::Replace($value, '(?i)(Authorization\s*[:=]\s*Bearer\s+)[A-Za-z0-9._~+/=-]+', '$1<REDACTED>')
    $value = [regex]::Replace($value, "(?i)((?:api[_-]?key|access[_-]?token|secret|password)\s*[:=]\s*[`"']?)[^\s,`"']+", '$1<REDACTED>')
    $value = [regex]::Replace($value, '\b(?:sk-[A-Za-z0-9_-]{16,}|gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,})\b', '<REDACTED_TOKEN>')
    $value = [regex]::Replace($value, '(?i)-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]*?-----END [A-Z ]*PRIVATE KEY-----', '<REDACTED_PRIVATE_KEY>')
    $value = [regex]::Replace($value, '\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', '<REDACTED_EMAIL>', 'IgnoreCase')
    $value = [regex]::Replace($value, '\b(?:10|127)\.(?:\d{1,3}\.){2}\d{1,3}\b|\b192\.168\.(?:\d{1,3}\.)\d{1,3}\b|\b172\.(?:1[6-9]|2\d|3[01])\.(?:\d{1,3}\.)\d{1,3}\b', '<REDACTED_LOCAL_IP>')
    return $value
}

$messages = [System.Collections.Generic.List[object]]::new()
$stream = [System.IO.FileStream]::new(
    $SourceJsonl,
    [System.IO.FileMode]::Open,
    [System.IO.FileAccess]::Read,
    [System.IO.FileShare]::ReadWrite -bor [System.IO.FileShare]::Delete)
$reader = [System.IO.StreamReader]::new($stream, [System.Text.Encoding]::UTF8, $true)
try {
while (($line = $reader.ReadLine()) -ne $null) {
    try { $record = $line | ConvertFrom-Json } catch { continue }
    if ($record.type -ne 'event_msg') { continue }

    if ($record.payload.type -eq 'user_message') {
        $messages.Add([pscustomobject]@{
            Timestamp = $record.timestamp
            Role = 'User'
            Text = Protect-PublicText ([string]$record.payload.message)
        })
    }
    elseif ($record.payload.type -eq 'agent_message' -and
            ($record.payload.phase -eq 'commentary' -or $record.payload.phase -eq 'final_answer')) {
        $messages.Add([pscustomobject]@{
            Timestamp = $record.timestamp
            Role = 'Assistant'
            Text = Protect-PublicText ([string]$record.payload.message)
        })
    }
}
}
finally {
    $reader.Dispose()
    $stream.Dispose()
}

New-Item -ItemType Directory -Force -Path $OutputDirectory | Out-Null
$markdownPath = Join-Path $OutputDirectory 'project-development-conversation.md'
$zipPath = Join-Path $OutputDirectory 'project-development-conversation.zip'

$builder = [System.Text.StringBuilder]::new()
[void]$builder.AppendLine('# AI Coding Session Manager - Public Development Conversation')
[void]$builder.AppendLine()
[void]$builder.AppendLine('This export contains only user messages and user-visible assistant responses from the main task. System/developer instructions, private reasoning, tool calls and outputs, subagent internal messages, authentication data, and machine caches are excluded.')
[void]$builder.AppendLine()
[void]$builder.AppendLine("Exported messages: $($messages.Count)")
[void]$builder.AppendLine()

foreach ($message in $messages) {
    [void]$builder.AppendLine("## $($message.Role) - $($message.Timestamp)")
    [void]$builder.AppendLine()
    [void]$builder.AppendLine($message.Text.Trim())
    [void]$builder.AppendLine()
}

[System.IO.File]::WriteAllText($markdownPath, $builder.ToString(), $utf8NoBom)
if (Test-Path -LiteralPath $zipPath) { Remove-Item -LiteralPath $zipPath -Force }
Compress-Archive -LiteralPath $markdownPath, (Join-Path $OutputDirectory 'README.md') -DestinationPath $zipPath -CompressionLevel Optimal

[pscustomobject]@{
    Messages = $messages.Count
    Markdown = $markdownPath
    Zip = $zipPath
    MarkdownBytes = (Get-Item -LiteralPath $markdownPath).Length
    ZipBytes = (Get-Item -LiteralPath $zipPath).Length
}
