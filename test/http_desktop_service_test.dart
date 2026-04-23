import 'dart:convert';
import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:super_ivan_pro/features/desktop_console/data/http_desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

void main() {
  test('loads desktop snapshot from local service status endpoint', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(server.close);

    server.listen((request) async {
      if (request.method == 'GET' && request.uri.path == '/status') {
        request.response
          ..statusCode = 200
          ..headers.contentType = ContentType.json
          ..write(
            jsonEncode({
              'service_state': 'running',
              'armed': true,
              'mode': 'rapid',
              'rule_pattern': 'START',
              'active_target': {
                'display_name': '文件传输助手',
                'talker': 'filehelper',
                'is_group': false,
              },
              'recent_events': [
                {
                  'chat_name': '文件传输助手',
                  'sender_name': '我',
                  'content': 'START',
                },
              ],
            }),
          );
        await request.response.close();
        return;
      }

      request.response.statusCode = 404;
      await request.response.close();
    });

    final service = HttpDesktopService(
      Uri.parse('http://${server.address.address}:${server.port}'),
    );

    final snapshot = await service.loadSnapshot();
    expect(snapshot.serviceStatusLabel, 'running');
    expect(snapshot.mode, DesktopMode.rapid);
    expect(snapshot.activeTarget.displayName, '文件传输助手');
  });

  test('posts mode updates to the local service', () async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0);
    addTearDown(server.close);

    String? body;
    server.listen((request) async {
      if (request.method == 'POST' && request.uri.path == '/mode') {
        body = await utf8.decoder.bind(request).join();
        request.response
          ..statusCode = 200
          ..headers.contentType = ContentType.json
          ..write('{}');
        await request.response.close();
        return;
      }

      request.response.statusCode = 404;
      await request.response.close();
    });

    final service = HttpDesktopService(
      Uri.parse('http://${server.address.address}:${server.port}'),
    );

    await service.saveMode(DesktopMode.rapid);

    expect(body, contains('"mode":"rapid"'));
  });
}
