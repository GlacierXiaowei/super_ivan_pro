import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/app/app.dart';

void main() {
  testWidgets('renders the desktop app title without the debug banner', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const SuperIvanDesktopApp());

    expect(find.text('微信自动化桌面端'), findsOneWidget);
    expect(find.text('DEBUG'), findsNothing);
  });
}
