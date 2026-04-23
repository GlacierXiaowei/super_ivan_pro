import 'package:flutter/material.dart';
import 'package:super_ivan_pro/app/theme.dart';
import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/data/http_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/presentation/desktop_console_page.dart';

class SuperIvanDesktopApp extends StatelessWidget {
  const SuperIvanDesktopApp({super.key, DesktopService? service})
    : _service = service;

  final DesktopService? _service;

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '微信自动化桌面端',
      debugShowCheckedModeBanner: false,
      theme: buildDesktopTheme(),
      home: DesktopConsolePage(
        service: _service ?? HttpDesktopService.development(),
      ),
    );
  }
}
