import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/controller/desktop_console_controller.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

void main() {
  test('saves the edited target and mode through the service', () async {
    final service = FakeDesktopService.seed();
    final controller = DesktopConsoleController(service);

    await controller.initialize();
    await controller.saveTarget(
      displayName: '多姆斯利普🌙',
      talker: '多姆斯利普🌙',
      isGroup: true,
    );
    await controller.setMode(DesktopMode.rapid);

    expect(service.lastSavedTarget?.displayName, '多姆斯利普🌙');
    expect(service.lastSavedMode, DesktopMode.rapid);
  });
}
