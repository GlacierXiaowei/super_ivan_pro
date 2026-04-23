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
    await _runBusy(() async {
      await _service.saveTarget(
        ActiveTarget(
          displayName: displayName,
          talker: talker,
          isGroup: isGroup,
        ),
      );
      await initialize();
    });
  }

  Future<void> saveRule({
    required String pattern,
    required List<String> replies,
    required int cooldownMs,
    required int maxTriggers,
  }) async {
    await _runBusy(() async {
      await _service.saveRule(
        DesktopRule(
          pattern: pattern,
          replies: replies,
          cooldownMs: cooldownMs,
          talker: snapshot?.activeTarget.talker ?? '',
          isGroup: snapshot?.activeTarget.isGroup ?? false,
        ),
      );
      final currentArmState = snapshot?.armState ?? DesktopSnapshot.seed().armState;
      await _service.saveArmState(
        currentArmState.copyWith(
          maxTriggers: maxTriggers,
          remainingTriggers: maxTriggers,
        ),
      );
      await initialize();
    });
  }

  Future<void> setArmed(bool enabled, {int? maxTriggers}) async {
    await _runBusy(() async {
      final currentArmState = snapshot?.armState ?? DesktopSnapshot.seed().armState;
      final nextMaxTriggers = maxTriggers ?? currentArmState.maxTriggers;
      await _service.saveArmState(
        currentArmState.copyWith(
          enabled: enabled,
          maxTriggers: nextMaxTriggers,
          remainingTriggers: nextMaxTriggers,
        ),
      );
      await initialize();
    });
  }

  Future<void> setMode(DesktopMode mode) async {
    await _runBusy(() async {
      await _service.saveMode(mode);
      await initialize();
    });
  }

  Future<void> startServices() async {
    await _runBusy(() async {
      await _service.startServices();
      await initialize();
    });
  }

  Future<void> stopServices() async {
    await _runBusy(() async {
      await _service.stopServices();
      await initialize();
    });
  }

  Future<void> _runBusy(Future<void> Function() action) async {
    isBusy = true;
    notifyListeners();
    try {
      await action();
    } finally {
      isBusy = false;
      notifyListeners();
    }
  }
}
