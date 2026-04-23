import 'package:flutter/foundation.dart';
import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class DesktopConsoleController extends ChangeNotifier {
  DesktopConsoleController(this._service);

  final DesktopService _service;
  DesktopSnapshot? snapshot;
  bool isBusy = false;

  Future<void> initialize() async {
    snapshot = await _service.loadSnapshot();
    notifyListeners();
  }

  Future<void> saveTarget({
    required String displayName,
    required String talker,
    required bool isGroup,
  }) async {
    await _service.saveTarget(
      ActiveTarget(
        displayName: displayName,
        talker: talker,
        isGroup: isGroup,
      ),
    );
    await initialize();
  }

  Future<void> setMode(DesktopMode mode) async {
    await _service.saveMode(mode);
    await initialize();
  }

  Future<void> startServices() async {
    isBusy = true;
    notifyListeners();
    try {
      await _service.startServices();
      await initialize();
    } finally {
      isBusy = false;
      notifyListeners();
    }
  }

  Future<void> stopServices() async {
    isBusy = true;
    notifyListeners();
    try {
      await _service.stopServices();
      await initialize();
    } finally {
      isBusy = false;
      notifyListeners();
    }
  }
}
