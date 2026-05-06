import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/controller/desktop_console_controller.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

void main() {
  test('saves the edited target, rule, and mode through the service', () async {
    final service = FakeDesktopService.seed();
    final controller = DesktopConsoleController(service);

    await controller.initialize();
    await controller.saveTarget(
      displayName: '多姆斯利普🌙',
      talker: '多姆斯利普🌙',
      isGroup: true,
    );
    await controller.setMode(DesktopMode.rapid);
    await controller.saveRule(
      pattern: 'GO',
      replies: ['第一条', '第二条'],
      cooldownMs: 120,
      maxTriggers: 3,
    );

    expect(service.lastSavedTarget?.displayName, '多姆斯利普🌙');
    expect(service.lastSavedMode, DesktopMode.rapid);
    expect(service.lastSavedRule?.pattern, 'GO');
    expect(service.lastSavedArmState?.maxTriggers, 3);
  });

  test('arms and disarms through the service', () async {
    final service = FakeDesktopService.seed();
    final controller = DesktopConsoleController(service);

    await controller.initialize();
    await controller.setArmed(true, maxTriggers: 2);
    expect(service.lastSavedArmState?.enabled, isTrue);
    expect(service.lastSavedArmState?.maxTriggers, 2);

    await controller.setArmed(false);
    expect(service.lastSavedArmState?.enabled, isFalse);
  });

  test(
    'restarts services through the service and refreshes snapshot',
    () async {
      final service = FakeDesktopService.seed();
      final controller = DesktopConsoleController(service);

      await controller.initialize();
      await controller.restartServices();

      expect(service.restartCallCount, 1);
      expect(controller.snapshot?.serviceStatusLabel, 'running');
    },
  );
}
