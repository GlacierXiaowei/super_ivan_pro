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

  @override
  Future<DesktopSnapshot> loadSnapshot() async => _snapshot;

  @override
  Future<void> saveMode(DesktopMode mode) async {
    lastSavedMode = mode;
    _snapshot = _snapshot.copyWith(mode: mode);
  }

  @override
  Future<void> saveRule(DesktopRule rule) async {
    lastSavedRule = rule;
    _snapshot = _snapshot.copyWith(rule: rule);
  }

  @override
  Future<void> saveArmState(DesktopArmState state) async {
    lastSavedArmState = state;
    _snapshot = _snapshot.copyWith(armState: state);
  }

  @override
  Future<void> saveTarget(ActiveTarget target) async {
    lastSavedTarget = target;
    _snapshot = _snapshot.copyWith(activeTarget: target);
  }

  @override
  Future<void> startServices() async {
    _snapshot = _snapshot.copyWith(serviceStatusLabel: 'running');
  }

  @override
  Future<void> restartServices() async {
    restartCallCount += 1;
    _snapshot = _snapshot.copyWith(serviceStatusLabel: 'running');
  }

  @override
  Future<void> stopServices() async {
    _snapshot = _snapshot.copyWith(serviceStatusLabel: 'stopped');
  }
}
