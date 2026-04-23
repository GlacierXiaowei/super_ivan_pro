import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

abstract class DesktopService {
  Future<DesktopSnapshot> loadSnapshot();
  Future<void> saveTarget(ActiveTarget target);
  Future<void> saveMode(DesktopMode mode);
}
