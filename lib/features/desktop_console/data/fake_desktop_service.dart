import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class FakeDesktopService implements DesktopService {
  FakeDesktopService.seed() : _snapshot = DesktopSnapshot.seed();

  DesktopSnapshot _snapshot;
  ActiveTarget? lastSavedTarget;
  DesktopMode lastSavedMode = DesktopMode.normal;

  @override
  Future<DesktopSnapshot> loadSnapshot() async => _snapshot;

  @override
  Future<void> saveMode(DesktopMode mode) async {
    lastSavedMode = mode;
    _snapshot = _snapshot.copyWith(mode: mode);
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
  Future<void> stopServices() async {
    _snapshot = _snapshot.copyWith(serviceStatusLabel: '本地服务未启动');
  }
}
