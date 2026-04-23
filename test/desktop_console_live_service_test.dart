import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/controller/desktop_console_controller.dart';
import 'package:super_ivan_pro/features/desktop_console/data/fake_desktop_service.dart';

class StubDesktopService extends FakeDesktopService {
  StubDesktopService() : super.seed();

  bool started = false;
  bool stopped = false;

  @override
  Future<void> startServices() async {
    started = true;
    await super.startServices();
  }

  @override
  Future<void> stopServices() async {
    stopped = true;
    await super.stopServices();
  }
}

void main() {
  test('start services updates controller busy state', () async {
    final service = StubDesktopService();
    final controller = DesktopConsoleController(service);

    await controller.startServices();

    expect(service.started, isTrue);
    expect(controller.isBusy, isFalse);
  });

  test('stop services updates controller busy state', () async {
    final service = StubDesktopService();
    final controller = DesktopConsoleController(service);

    await controller.stopServices();

    expect(service.stopped, isTrue);
    expect(controller.isBusy, isFalse);
  });
}
