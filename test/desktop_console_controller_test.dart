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
      matchMode: DesktopMatchMode.regex,
      replyDelayMs: 250,
      sender: '',
    );

    expect(service.lastSavedTarget?.displayName, '多姆斯利普🌙');
    expect(service.lastSavedMode, DesktopMode.rapid);
    expect(service.lastSavedRule?.pattern, 'GO');
    expect(service.lastSavedRule?.replyDelayMs, 250);
    expect(service.lastSavedArmState?.maxTriggers, 3);
  });

  test('saves arbitrary trigger rule through the service', () async {
    final service = FakeDesktopService.seed();
    final controller = DesktopConsoleController(service);

    await controller.initialize();
    await controller.saveRule(
      pattern: '',
      replies: ['收到'],
      cooldownMs: 0,
      maxTriggers: 5,
      matchMode: DesktopMatchMode.any,
      replyDelayMs: 0,
      sender: '',
    );

    expect(service.lastSavedRule?.matchMode, DesktopMatchMode.any);
    expect(service.lastSavedRule?.toRulePayload()['match_mode'], 'any');
    expect(service.lastSavedRule?.toRulePayload()['type'], 'unknown');
  });

  test('saves selected history sender as rule sender filter', () async {
    final service = FakeDesktopService.seed();
    final controller = DesktopConsoleController(service);

    await controller.initialize();
    final candidates = await controller.searchHistorySenders(
      chat: '123456@chatroom',
      query: 'Alice',
    );
    await controller.setRuleSenderFilter(
      sender: candidates.single.sender,
      senderName: candidates.single.senderName,
    );

    expect(candidates.single.sender, 'wxid_alice');
    expect(service.lastSavedRule?.sender, 'wxid_alice');
    expect(service.lastSavedRule?.senderName, 'Alice Remark');
    expect(service.lastSavedRule?.toRulePayload()['sender'], 'wxid_alice');
  });

  test('searches history chats and saves selected chat target', () async {
    final service = FakeDesktopService.seed();
    final controller = DesktopConsoleController(service);

    await controller.initialize();
    final candidates = await controller.searchHistoryChats(query: '项目');
    await controller.saveTarget(
      displayName: candidates.single.displayName,
      talker: candidates.single.talker,
      isGroup: true,
    );

    expect(service.lastHistoryChatSearchQuery, '项目');
    expect(candidates.single.talker, '123456@chatroom');
    expect(service.lastSavedTarget?.displayName, '项目讨论群');
    expect(service.lastSavedTarget?.talker, '123456@chatroom');
    expect(service.lastSavedTarget?.isGroup, isTrue);
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
