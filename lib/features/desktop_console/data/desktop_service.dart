import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

abstract class DesktopService {
  Future<DesktopSnapshot> loadSnapshot();
  Future<DesktopSnapshot> saveTarget(ActiveTarget target);
  Future<DesktopSnapshot> saveRule(DesktopRule rule);
  Future<DesktopSnapshot> saveArmState(DesktopArmState state);
  Future<DesktopSnapshot> saveMode(DesktopMode mode);
  Future<List<HistorySenderCandidate>> searchHistorySenders({
    required String chat,
    required String query,
    int limit = 20,
  });
  Future<List<HistoryChatCandidate>> searchHistoryChats({
    required String query,
    int limit = 20,
  });
  Future<DesktopSnapshot> startServices();
  Future<DesktopSnapshot> restartServices();
  Future<DesktopSnapshot> stopServices();
}
