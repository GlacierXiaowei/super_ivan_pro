import 'dart:async';
import 'dart:convert';
import 'dart:io';

import 'package:super_ivan_pro/features/desktop_console/data/desktop_service.dart';
import 'package:super_ivan_pro/features/desktop_console/data/windows_service_launcher.dart';
import 'package:super_ivan_pro/features/desktop_console/models/desktop_models.dart';

class HttpDesktopService implements DesktopService {
  HttpDesktopService(
    this._baseUri, {
    HttpClient? client,
    WindowsServiceLauncher? launcher,
  }) : _client = client ?? HttpClient(),
       _launcher = launcher;

  factory HttpDesktopService.development() {
    const host = '127.0.0.1';
    const port = 18090;
    return HttpDesktopService(
      Uri.parse('http://$host:$port'),
      launcher: WindowsServiceLauncher(
        workspaceRoot: WindowsServiceLauncher.resolveWorkspaceRoot(),
        pythonExecutable:
            Platform.environment['SUPER_IVAN_DESKTOP_PYTHON'] ?? 'python',
        host: host,
        port: port,
      ),
    );
  }

  final Uri _baseUri;
  final HttpClient _client;
  final WindowsServiceLauncher? _launcher;

  @override
  Future<DesktopSnapshot> loadSnapshot() async {
    try {
      final payload = await _requestJson('GET', '/status');
      return DesktopSnapshot.fromJson(payload);
    } on SocketException {
      if (_launcher == null) {
        return DesktopSnapshot.offline();
      }
      await _launcher.start();
      await _waitUntilAvailable();
      final payload = await _requestJson('GET', '/status');
      return DesktopSnapshot.fromJson(payload);
    } on HttpException {
      return DesktopSnapshot.offline();
    }
  }

  @override
  Future<void> saveTarget(ActiveTarget target) async {
    await _ensureServerRunning();
    await _requestJson('POST', '/targets/active', body: target.toJson());
  }

  @override
  Future<void> saveRule(DesktopRule rule) async {
    await _ensureServerRunning();
    await _requestJson('POST', '/rules', body: {'rules': [rule.toRulePayload()]});
  }

  @override
  Future<void> saveArmState(DesktopArmState state) async {
    await _ensureServerRunning();
    await _requestJson('POST', '/arm-state', body: state.toJson());
  }

  @override
  Future<void> saveMode(DesktopMode mode) async {
    await _ensureServerRunning();
    await _requestJson('POST', '/mode', body: {'mode': mode.name});
  }

  @override
  Future<void> startServices() async {
    await _ensureServerRunning();
    await _requestJson('POST', '/services/start');
  }

  @override
  Future<void> stopServices() async {
    await _ensureServerRunning();
    await _requestJson('POST', '/services/stop');
  }

  Future<void> _ensureServerRunning() async {
    try {
      await _requestJson('GET', '/status');
    } on SocketException {
      final launcher = _launcher;
      if (launcher == null) {
        rethrow;
      }
      await launcher.start();
      await _waitUntilAvailable();
    } on HttpException {
      if (_launcher == null) {
        return;
      }
    }
  }

  Future<void> _waitUntilAvailable() async {
    final deadline = DateTime.now().add(const Duration(seconds: 5));
    while (DateTime.now().isBefore(deadline)) {
      try {
        await _requestJson('GET', '/status');
        return;
      } on SocketException {
        await Future<void>.delayed(const Duration(milliseconds: 150));
      } on HttpException {
        await Future<void>.delayed(const Duration(milliseconds: 150));
      }
    }

    throw StateError('desktop_service_not_available');
  }

  Future<Map<String, dynamic>> _requestJson(
    String method,
    String path, {
    Map<String, dynamic>? body,
  }) async {
    final request = switch (method) {
      'GET' => await _client.getUrl(_baseUri.resolve(path)),
      'POST' => await _client.postUrl(_baseUri.resolve(path)),
      _ => throw UnsupportedError('unsupported method: $method'),
    };

    if (body != null) {
      final encoded = utf8.encode(jsonEncode(body));
      request.headers.contentType = ContentType.json;
      request.contentLength = encoded.length;
      request.add(encoded);
    }

    final response = await request.close();
    final text = await response.transform(utf8.decoder).join();
    final payload = text.isEmpty
        ? <String, dynamic>{}
        : jsonDecode(text) as Map<String, dynamic>;

    if (response.statusCode >= 400) {
      throw HttpException(
        'request failed: ${response.statusCode}',
        uri: _baseUri.resolve(path),
      );
    }

    return payload;
  }
}
