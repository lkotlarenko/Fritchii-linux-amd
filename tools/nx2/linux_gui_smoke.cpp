// SPDX-FileCopyrightText: Copyright 2026 Fritchii Linux contributors
// SPDX-License-Identifier: GPL-3.0-or-later

#include <QAction>
#include <QApplication>
#include <QDialog>
#include <QFile>
#include <QGuiApplication>
#include <QMainWindow>
#include <QTextStream>
#include <QTimer>
#include <dlfcn.h>

namespace {
void Record(const QString& message) {
    QFile file(qEnvironmentVariable("FRITCHII_SMOKE_REPORT"));
    if (file.open(QIODevice::Append | QIODevice::Text)) {
        QTextStream(&file) << message << '\n';
    }
}
} // namespace

// Loaded only by test-linux-appimage.sh, with a newly created empty profile.
int QDialog::exec() {
    using Function = int (*)(QDialog*);
    static const auto run = reinterpret_cast<Function>(dlsym(RTLD_NEXT, "_ZN7QDialog4execEv"));
    Record("dialog=" + QString(metaObject()->className()));
    QTimer::singleShot(500, this, [this] { accept(); });
    return run(this);
}

int QApplication::exec() {
    using Function = int (*)();
    static const auto run = reinterpret_cast<Function>(dlsym(RTLD_NEXT, "_ZN12QApplication4execEv"));
    Record("platform=" + QGuiApplication::platformName());
    QTimer::singleShot(4000, qApp, [] {
        for (auto* widget : QApplication::topLevelWidgets()) {
            if (!qobject_cast<QMainWindow*>(widget) || !widget->isVisible()) {
                continue;
            }
            Record("main=" + widget->windowTitle());
            for (auto* action : widget->findChildren<QAction*>()) {
                if (action->objectName() == "action_Configure") {
                    action->trigger();
                    Record("settings=opened");
                    break;
                }
            }
        }
        QTimer::singleShot(500, qApp, [] {
            QApplication::closeAllWindows();
            QApplication::quit();
        });
    });
    QTimer::singleShot(20000, qApp, [] { QApplication::exit(2); });
    return run();
}
