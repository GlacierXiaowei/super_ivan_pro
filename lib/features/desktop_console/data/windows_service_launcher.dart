import 'dart:async';
import 'dart:io';

class LaunchCommand {
  const LaunchCommand({
    required this.executable,
    required this.arguments,
    required this.workingDirectory,
  });

  final String executable;
  final List<String> arguments;
  final String workingDirectory;
}

class WindowsServiceLauncher {
  WindowsServiceLauncher({
    required this.serviceRoot,
    required this.pythonExecutable,
    this.host = '127.0.0.1',
    this.port = 18090,
  });

  static const _sourceServiceRoot =
      'android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation';

  final String serviceRoot;
  final String pythonExecutable;
  final String host;
  final int port;

  Process? _process;

  static String resolveServiceRoot({List<Directory>? seeds}) {
    final env = Platform.environment['SUPER_IVAN_WECHAT_AUTOMATION_ROOT'];
    if (env != null && env.trim().isNotEmpty) {
      return env;
    }

    final candidates =
        seeds ??
        <Directory>[
          Directory.current,
          File(Platform.resolvedExecutable).parent,
        ];
    for (final seed in candidates) {
      for (
        Directory? current = seed;
        current != null;
        current = current.parent == current ? null : current.parent
      ) {
        final sourceRoot = Directory('${current.path}/$_sourceServiceRoot');
        if (_hasDesktopServiceScript(sourceRoot)) {
          return sourceRoot.path;
        }

        final bundledRoot = Directory(
          '${current.path}/data/flutter_assets/$_sourceServiceRoot',
        );
        if (_hasDesktopServiceScript(bundledRoot)) {
          return bundledRoot.path;
        }

        final debugBundledRoot = Directory(
          '${current.path}/flutter_assets/$_sourceServiceRoot',
        );
        if (_hasDesktopServiceScript(debugBundledRoot)) {
          return debugBundledRoot.path;
        }
      }
    }

    return '${Directory.current.path}/$_sourceServiceRoot';
  }

  static bool _hasDesktopServiceScript(Directory root) {
    return File('${root.path}/scripts/desktop_service.py').existsSync();
  }

  LaunchCommand buildStartCommand() {
    final scriptPath = '$serviceRoot/scripts/desktop_service.py';
    return LaunchCommand(
      executable: pythonExecutable,
      arguments: [scriptPath, '--host', host, '--port', '$port'],
      workingDirectory: serviceRoot,
    );
  }

  Future<void> start() async {
    if (_process != null) {
      return;
    }

    final command = buildStartCommand();
    _process = await Process.start(
      command.executable,
      command.arguments,
      workingDirectory: command.workingDirectory,
      runInShell: true,
    );
  }

  Future<void> stop() async {
    final process = _process;
    _process = null;
    if (process == null) {
      return;
    }

    process.kill();
    try {
      await process.exitCode.timeout(const Duration(seconds: 2));
    } on TimeoutException {
      process.kill(ProcessSignal.sigkill);
    }
  }
}
