import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/app/app.dart';
import 'package:super_ivan_pro/core/modules/app_module.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';

void main() {
  testWidgets('renders the existing desktop console when no modules exist', (
    tester,
  ) async {
    await tester.pumpWidget(
      SuperIvanDesktopApp(
        service: FakeDesktopService.seed(),
        modules: const <AppModule>[],
      ),
    );

    expect(find.text('微信自动化桌面端'), findsOneWidget);
    expect(find.text('服务状态'), findsOneWidget);
    expect(find.byType(NavigationRail), findsNothing);
  });

  testWidgets('renders an injected module through the module host', (
    tester,
  ) async {
    final modules = <AppModule>[
      AppModule(
        id: 'synthetic',
        title: '测试模块',
        description: 'Only used by widget tests.',
        icon: Icons.extension,
        builder: (_) => const Center(child: Text('测试模块内容')),
      ),
    ];

    await tester.pumpWidget(
      SuperIvanDesktopApp(service: FakeDesktopService.seed(), modules: modules),
    );

    expect(find.byType(NavigationRail), findsOneWidget);
    expect(find.text('控制台'), findsOneWidget);
    expect(find.text('测试模块'), findsOneWidget);

    await tester.tap(find.text('测试模块'));
    await tester.pumpAndSettle();

    expect(find.text('测试模块内容'), findsOneWidget);
  });
}
