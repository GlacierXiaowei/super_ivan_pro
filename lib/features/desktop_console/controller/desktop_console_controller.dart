import 'package:flutter/foundation.dart';
import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class DesktopConsoleController extends ChangeNotifier {
  DesktopConsoleController(this._service);

  final DesktopService _service;
  DesktopSnapshot? snapshot;
  bool isBusy = false;
  bool _disposed = false;

  Future<void> initialize() async {
    final nextSnapshot = await _service.loadSnapshot();
    if (_disposed) {
      return;
    }
    _setSnapshot(nextSnapshot);
  }

  Future<void> saveTarget({
    required String displayName,
    required String talker,
    required bool isGroup,
  }) async {
    await _runBusy(() async {
      final nextSnapshot = await _service.saveTarget(
        ActiveTarget(
          displayName: displayName,
          talker: talker,
          isGroup: isGroup,
        ),
      );
      snapshot = nextSnapshot;
    });
  }

  Future<void> saveRule({
    required String pattern,
    required List<String> replies,
    required int cooldownMs,
    required int maxTriggers,
  }) async {
    await _runBusy(() async {
      final ruleSnapshot = await _service.saveRule(
        DesktopRule(
          pattern: pattern,
          replies: replies,
          cooldownMs: cooldownMs,
          talker: snapshot?.activeTarget.talker ?? '',
          isGroup: snapshot?.activeTarget.isGroup ?? false,
        ),
      );
      final currentArmState = ruleSnapshot.armState;
      final nextSnapshot = await _service.saveArmState(
        currentArmState.copyWith(
          maxTriggers: maxTriggers,
          remainingTriggers: maxTriggers,
        ),
      );
      snapshot = nextSnapshot;
    });
  }

  Future<void> setArmed(bool enabled, {int? maxTriggers}) async {
    await _runBusy(() async {
      final currentArmState =
          snapshot?.armState ?? DesktopSnapshot.seed().armState;
      final nextMaxTriggers = maxTriggers ?? currentArmState.maxTriggers;
      final nextSnapshot = await _service.saveArmState(
        currentArmState.copyWith(
          enabled: enabled,
          maxTriggers: nextMaxTriggers,
          remainingTriggers: nextMaxTriggers,
        ),
      );
      snapshot = nextSnapshot;
    });
  }

  Future<void> setMode(DesktopMode mode) async {
    await _runBusy(() async {
      snapshot = await _service.saveMode(mode);
    });
  }

  Future<void> startServices() async {
    await _runBusy(() async {
      snapshot = await _service.startServices();
    });
  }

  Future<void> restartServices() async {
    await _runBusy(() async {
      snapshot = await _service.restartServices();
    });
  }

  Future<void> stopServices() async {
    await _runBusy(() async {
      snapshot = await _service.stopServices();
    });
  }

  Future<void> _runBusy(Future<void> Function() action) async {
    isBusy = true;
    notifyListeners();
    try {
      await action();
    } finally {
      if (!_disposed) {
        isBusy = false;
        notifyListeners();
      }
    }
  }

  @override
  void dispose() {
    _disposed = true;
    super.dispose();
  }

  void _setSnapshot(DesktopSnapshot nextSnapshot) {
    snapshot = nextSnapshot;
    notifyListeners();
  }
}
