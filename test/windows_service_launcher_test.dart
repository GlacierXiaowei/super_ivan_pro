import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/data/windows_service_launcher.dart';

void main() {
  test('builds the python desktop service command with the expected workspace script', () {
    final launcher = WindowsServiceLauncher(
      workspaceRoot: r'D:\flutter_app\super_ivan_pro',
      pythonExecutable: 'python',
    );

    final command = launcher.buildStartCommand();
    expect(command.executable, 'python');
    expect(command.arguments.first, contains('scripts/desktop_service.py'));
    expect(command.arguments, containsAll(['--host', '127.0.0.1', '--port', '18090']));
  });
}
