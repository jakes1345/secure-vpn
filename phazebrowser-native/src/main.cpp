#include <QApplication>
#include <QStyleFactory>
#include <QPalette>
#include <QColor>
#include "mainwindow.h"

int main(int argc, char *argv[])
{
    QApplication app(argc, argv);
    
    // Set application info
    app.setApplicationName("PhazeBrowser");
    app.setApplicationVersion("2.0.0");
    app.setOrganizationName("PhazeVPN");
    
    // Set dark theme
    app.setStyle(QStyleFactory::create("Fusion"));
    
    QPalette darkPalette;
    darkPalette.setColor(QPalette::Window, QColor(30, 30, 30));
    darkPalette.setColor(QPalette::WindowText, Qt::white);
    darkPalette.setColor(QPalette::Base, QColor(45, 45, 45));
    darkPalette.setColor(QPalette::AlternateBase, QColor(53, 53, 53));
    darkPalette.setColor(QPalette::ToolTipBase, Qt::white);
    darkPalette.setColor(QPalette::ToolTipText, Qt::white);
    darkPalette.setColor(QPalette::Text, Qt::white);
    darkPalette.setColor(QPalette::Button, QColor(45, 45, 45));
    darkPalette.setColor(QPalette::ButtonText, Qt::white);
    darkPalette.setColor(QPalette::BrightText, Qt::red);
    darkPalette.setColor(QPalette::Link, QColor(0, 120, 212));
    darkPalette.setColor(QPalette::Highlight, QColor(0, 120, 212));
    darkPalette.setColor(QPalette::HighlightedText, Qt::black);
    app.setPalette(darkPalette);
    
    MainWindow window;
    window.show();
    
    return app.exec();
}
