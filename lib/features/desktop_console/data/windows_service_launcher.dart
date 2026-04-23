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
    required this.workspaceRoot,
    required this.pythonExecutable,
    this.host = '127.0.0.1',
    this.port = 18090,
  });

  final String workspaceRoot;
  final String pythonExecutable;
  final String host;
  final int port;

  Process? _process;

  static String resolveWorkspaceRoot() {
    final env = Platform.environment['SUPER_IVAN_WORKSPACE_ROOT'];
    if (env != null && env.trim().isNotEmpty) {
      return env;
    }

    final candidates = <Directory>[
      Directory.current,
      File(Platform.resolvedExecutable).parent,
    ];
    for (final seed in candidates) {
      for (
        Directory? current = seed;
        current != null;
        current = current.parent == current ? null : current.parent
      ) {
        final marker = File(
          '${current.path}/android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/desktop_service.py',
        );
        if (marker.existsSync()) {
          return current.path;
        }
      }
    }

    return Directory.current.path;
  }

  LaunchCommand buildStartCommand() {
    final scriptPath =
        '$workspaceRoot/android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation/scripts/desktop_service.py';
    return LaunchCommand(
      executable: pythonExecutable,
      arguments: [
        scriptPath,
        '--host',
        host,
        '--port',
        '$port',
      ],
      workingDirectory: workspaceRoot,
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
