import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class FakeDesktopService implements DesktopService {
  FakeDesktopService.seed() : _snapshot = DesktopSnapshot.seed();

  DesktopSnapshot _snapshot;
  ActiveTarget? lastSavedTarget;
  DesktopRule? lastSavedRule;
  DesktopArmState? lastSavedArmState;
  DesktopMode lastSavedMode = DesktopMode.normal;
  int restartCallCount = 0;
  String? lastHistorySearchChat;
  String? lastHistorySearchQuery;
  String? lastHistoryChatSearchQuery;

  @override
  Future<DesktopSnapshot> loadSnapshot() async => _snapshot;

  @override
  Future<DesktopSnapshot> saveMode(DesktopMode mode) async {
    lastSavedMode = mode;
    _snapshot = _snapshot.copyWith(mode: mode);
    return _snapshot;
  }

  @override
  Future<DesktopSnapshot> saveRule(DesktopRule rule) async {
    lastSavedRule = rule;
    _snapshot = _snapshot.copyWith(rule: rule);
    return _snapshot;
  }

  @override
  Future<DesktopSnapshot> saveArmState(DesktopArmState state) async {
    lastSavedArmState = state;
    _snapshot = _snapshot.copyWith(armState: state);
    return _snapshot;
  }

  @override
  Future<DesktopSnapshot> saveTarget(ActiveTarget target) async {
    lastSavedTarget = target;
    _snapshot = _snapshot.copyWith(activeTarget: target);
    return _snapshot;
  }

  @override
  Future<List<HistorySenderCandidate>> searchHistorySenders({
    required String chat,
    required String query,
    int limit = 20,
  }) async {
    lastHistorySearchChat = chat;
    lastHistorySearchQuery = query;
    return const [
      HistorySenderCandidate(
        sender: 'wxid_alice',
        senderName: 'Alice Remark',
        lastTimestamp: 1778000003,
        lastContent: '最近一条历史发言',
        messageCount: 2,
      ),
    ];
  }

  @override
  Future<List<HistoryChatCandidate>> searchHistoryChats({
    required String query,
    int limit = 20,
  }) async {
    lastHistoryChatSearchQuery = query;
    return const [
      HistoryChatCandidate(
        talker: '123456@chatroom',
        displayName: '项目讨论群',
        lastTimestamp: 1778000004,
        summary: '最近一条群消息',
        source: 'session',
      ),
    ];
  }

  @override
  Future<DesktopSnapshot> startServices() async {
    _snapshot = _snapshot.copyWith(serviceStatusLabel: 'running');
    return _snapshot;
  }

  @override
  Future<DesktopSnapshot> restartServices() async {
    restartCallCount += 1;
    _snapshot = _snapshot.copyWith(serviceStatusLabel: 'running');
    return _snapshot;
  }

  @override
  Future<DesktopSnapshot> stopServices() async {
    _snapshot = _snapshot.copyWith(serviceStatusLabel: 'stopped');
    return _snapshot;
  }
}
