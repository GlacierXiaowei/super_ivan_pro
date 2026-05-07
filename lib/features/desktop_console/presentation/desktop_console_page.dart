import 'dart:async';

import 'package:flutter/material.dart';
import 'package:super_ivan_pro/features/desktop_console/controller/desktop_console_controller.dart';
import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/events_panel.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/mode_panel.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/rule_panel.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/status_panel.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/widgets/target_panel.dart';

class DesktopConsolePage extends StatefulWidget {
  const DesktopConsolePage({super.key, required this.service});

  final DesktopService service;

  @override
  State<DesktopConsolePage> createState() => _DesktopConsolePageState();
}

class _DesktopConsolePageState extends State<DesktopConsolePage> {
  late final DesktopConsoleController controller;
  Timer? _refreshTimer;
  bool _refreshInFlight = false;

  @override
  void initState() {
    super.initState();
    controller = DesktopConsoleController(widget.service);
    controller.initialize();
    _refreshTimer = Timer.periodic(const Duration(seconds: 1), (_) {
      if (!mounted || controller.isBusy || _refreshInFlight) {
        return;
      }
      _refreshInFlight = true;
      controller.initialize().whenComplete(() {
        _refreshInFlight = false;
      });
    });
  }

  @override
  void dispose() {
    _refreshTimer?.cancel();
    controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: controller,
      builder: (context, _) {
        final snapshot = controller.snapshot ?? DesktopSnapshot.offline();
        return Scaffold(
          appBar: AppBar(title: const Text('微信自动化桌面端')),
          body: ListView(
            padding: const EdgeInsets.all(20),
            children: [
              StatusPanel(
                snapshot: snapshot,
                isBusy: controller.isBusy,
                onStartPressed: controller.startServices,
                onRestartPressed: controller.restartServices,
                onStopPressed: controller.stopServices,
                onArmPressed: () => controller.setArmed(
                  true,
                  maxTriggers: snapshot.armState.maxTriggers,
                ),
                onDisarmPressed: () => controller.setArmed(false),
              ),
              const SizedBox(height: 16),
              TargetPanel(
                snapshot: snapshot,
                isBusy: controller.isBusy,
                onSaveTarget: controller.saveTarget,
                onSearchHistoryChats: controller.searchHistoryChats,
                onSearchHistorySenders: controller.searchHistorySenders,
                onSelectSender: controller.setRuleSenderFilter,
              ),
              const SizedBox(height: 16),
              RulePanel(
                snapshot: snapshot,
                isBusy: controller.isBusy,
                onSaveRule: controller.saveRule,
              ),
              const SizedBox(height: 16),
              ModePanel(
                snapshot: snapshot,
                isBusy: controller.isBusy,
                onModeChanged: controller.setMode,
              ),
              const SizedBox(height: 16),
              EventsPanel(snapshot: snapshot),
            ],
          ),
        );
      },
    );
  }
}
