import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

abstract class DesktopService {
  Future<DesktopSnapshot> loadSnapshot();
  Future<void> saveTarget(ActiveTarget target);
  Future<void> saveRule(DesktopRule rule);
  Future<void> saveArmState(DesktopArmState state);
  Future<void> saveMode(DesktopMode mode);
  Future<void> startServices();
  Future<void> restartServices();
  Future<void> stopServices();
}
