# NewAPI Client Configurator (.NET)

This is the Windows desktop rewrite of the Python tool.

## Build

```powershell
cd dotnet
C:\Program Files\dotnet\dotnet.exe build
```

## Publish a single-file exe for Windows 10

```powershell
cd dotnet
C:\Program Files\dotnet\dotnet.exe publish src\NewAPIClientConfigurator.App\NewAPIClientConfigurator.App.csproj -c Release -r win-x64 --self-contained true /p:PublishSingleFile=true
```

The published executable will be under the `bin\Release\net8.0-windows\win-x64\publish` folder.
