import 'package:flutter/material.dart';
import 'package:super_ivan_pro/app/theme.dart';

class SuperIvanDesktopApp extends StatelessWidget {
  const SuperIvanDesktopApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: '微信自动化桌面端',
      debugShowCheckedModeBanner: false,
      theme: buildDesktopTheme(),
      home: const _DesktopBootstrapPage(),
    );
  }
}

class _DesktopBootstrapPage extends StatelessWidget {
  const _DesktopBootstrapPage();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('微信自动化桌面端'),
      ),
      body: const Padding(
        padding: EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('服务状态'),
            SizedBox(height: 12),
            Text('监听对象'),
            SizedBox(height: 12),
            Text('规则配置'),
          ],
        ),
      ),
    );
  }
}
