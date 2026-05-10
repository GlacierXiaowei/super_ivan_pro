import 'package:flutter/material.dart';

class AppModule {
  const AppModule({
    required this.id,
    required this.title,
    required this.icon,
    required this.builder,
    this.description,
  });

  final String id;
  final String title;
  final String? description;
  final IconData icon;
  final WidgetBuilder builder;

  Widget build(BuildContext context) => builder(context);
}
