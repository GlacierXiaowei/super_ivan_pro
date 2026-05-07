import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/data/windows_service_launcher.dart';

void main() {
  test(
    'builds the python desktop service command with the expected service script',
    () {
      final launcher = WindowsServiceLauncher(
        serviceRoot:
            r'D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation',
        pythonExecutable: 'python',
      );

      final command = launcher.buildStartCommand();
      expect(command.executable, 'python');
      expect(command.arguments.first, contains('scripts/desktop_service.py'));
      expect(command.workingDirectory, contains('wechat_automation'));
      expect(
        command.arguments,
        containsAll(['--host', '127.0.0.1', '--port', '18090']),
      );
    },
  );

  test('resolves the bundled flutter asset service root', () async {
    final temp = await Directory.systemTemp.createTemp('super_ivan_launcher_');
    addTearDown(() async {
      if (temp.existsSync()) {
        await temp.delete(recursive: true);
      }
    });

    final serviceRoot = Directory(
      '${temp.path}/data/flutter_assets/android/app/src/main/kotlin/com/super_ivan_pro/glacier/wechat_automation',
    );
    await Directory('${serviceRoot.path}/scripts').create(recursive: true);
    await File(
      '${serviceRoot.path}/scripts/desktop_service.py',
    ).writeAsString('');

    expect(
      WindowsServiceLauncher.resolveServiceRoot(seeds: [temp]),
      serviceRoot.path,
    );
  });

  test('falls back to py launcher when python command probe fails', () {
    final command = WindowsServiceLauncher.resolvePythonCommand(
      environment: const {},
      commandWorks: (executable, arguments) => executable == 'py',
    );

    expect(command.executable, 'py');
    expect(command.argumentsPrefix, ['-3']);
  });

  test('builds service command with python prefix arguments', () {
    final launcher = WindowsServiceLauncher(
      serviceRoot:
          r'D:\flutter_app\super_ivan_pro\android\app\src\main\kotlin\com\super_ivan_pro\glacier\wechat_automation',
      pythonExecutable: 'py',
      pythonArgumentsPrefix: const ['-3'],
    );

    final command = launcher.buildStartCommand();
    expect(command.executable, 'py');
    expect(command.arguments.first, '-3');
    expect(command.arguments[1], contains('scripts/desktop_service.py'));
  });

  test('prefers explicit python environment override', () {
    final command = WindowsServiceLauncher.resolvePythonCommand(
      environment: const {
        'SUPER_IVAN_DESKTOP_PYTHON': r'C:\Python312\python.exe',
      },
      commandWorks: (_, _) => false,
    );

    expect(command.executable, r'C:\Python312\python.exe');
    expect(command.argumentsPrefix, isEmpty);
  });

  test('falls back to python command when no probe succeeds', () {
    final command = WindowsServiceLauncher.resolvePythonCommand(
      environment: const {},
      commandWorks: (_, _) => false,
    );

    expect(command.executable, 'python');
    expect(command.argumentsPrefix, isEmpty);
  });

  test('resolvePythonExecutable keeps legacy python executable API', () {
    expect(
      WindowsServiceLauncher.resolvePythonExecutable(
        environment: const {
          'SUPER_IVAN_DESKTOP_PYTHON': r'C:\Python312\python.exe',
        },
      ),
      r'C:\Python312\python.exe',
    );
  });
}
