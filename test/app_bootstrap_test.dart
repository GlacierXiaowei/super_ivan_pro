import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/app/app.dart';

void main() {
  testWidgets('boots the windows desktop console shell', (tester) async {
    await tester.pumpWidget(const SuperIvanDesktopApp());

    expect(find.text('微信自动化桌面端'), findsOneWidget);
    expect(find.text('服务状态'), findsOneWidget);
    expect(find.text('监听对象'), findsOneWidget);
    expect(find.text('规则配置'), findsOneWidget);
  });
}
