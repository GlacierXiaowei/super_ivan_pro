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

class PythonCommand {
  const PythonCommand({
    required this.executable,
    this.argumentsPrefix = const [],
  });

  final String executable;
  final List<String> argumentsPrefix;
}

class WindowsServiceLauncher {
  WindowsServiceLauncher({
    required this.serviceRoot,
    required this.pythonExecutable,
    this.pythonArgumentsPrefix = const [],
    this.host = '127.0.0.1',
    this.port = 18090,
  });

  static const _sourceServiceRoot =
      'android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation';

  final String serviceRoot;
  final String pythonExecutable;
  final List<String> pythonArgumentsPrefix;
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

  static String resolvePythonExecutable({Map<String, String>? environment}) {
    return resolvePythonCommand(environment: environment).executable;
  }

  static PythonCommand resolvePythonCommand({
    Map<String, String>? environment,
    bool Function(String executable, List<String> arguments)? commandWorks,
  }) {
    final envMap = environment ?? Platform.environment;
    final env = envMap['SUPER_IVAN_DESKTOP_PYTHON'];
    if (env != null && env.trim().isNotEmpty) {
      return PythonCommand(executable: env);
    }

    final works = commandWorks ?? _commandWorks;
    if (works('python', const ['--version'])) {
      return const PythonCommand(executable: 'python');
    }
    if (works('py', const ['-3', '--version'])) {
      return const PythonCommand(executable: 'py', argumentsPrefix: ['-3']);
    }
    return const PythonCommand(executable: 'python');
  }

  static bool _hasDesktopServiceScript(Directory root) {
    return File('${root.path}/scripts/desktop_service.py').existsSync();
  }

  LaunchCommand buildStartCommand() {
    final scriptPath = '$serviceRoot/scripts/desktop_service.py';
    return LaunchCommand(
      executable: pythonExecutable,
      arguments: [
        ...pythonArgumentsPrefix,
        scriptPath,
        '--host',
        host,
        '--port',
        '$port',
      ],
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

  static bool _commandWorks(String executable, List<String> arguments) {
    try {
      final result = Process.runSync(executable, arguments, runInShell: true);
      return result.exitCode == 0;
    } on Object {
      return false;
    }
  }
}
