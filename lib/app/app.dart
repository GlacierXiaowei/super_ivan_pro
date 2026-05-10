import 'package:flutter/material.dart';
import 'package:super_ivan_pro/app/theme.dart';
import 'package:super_ivan_pro/core/modules/app_module.dart';
import 'package:super_ivan_pro/core/modules/module_host_page.dart';
import 'package:super_ivan_pro/edition/module_registry.dart';
import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/data/http_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/desktop_console_page.dart';

class SuperIvanDesktopApp extends StatelessWidget {
  const SuperIvanDesktopApp({
    super.key,
    DesktopService? service,
    List<AppModule>? modules,
  }) : _service = service,
       _modules = modules;

  final DesktopService? _service;
  final List<AppModule>? _modules;

  @override
  Widget build(BuildContext context) {
    final service = _service ?? HttpDesktopService.development();
    final modules = _modules ?? buildEditionModules();
    final desktopConsole = DesktopConsolePage(service: service);

    return MaterialApp(
      title: '微信自动化桌面端',
      debugShowCheckedModeBanner: false,
      theme: buildDesktopTheme(),
      home: modules.isEmpty
          ? desktopConsole
          : ModuleHostPage(desktopConsole: desktopConsole, modules: modules),
    );
  }
}
