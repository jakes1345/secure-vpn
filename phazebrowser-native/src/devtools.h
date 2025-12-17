#ifndef DEVTOOLS_H
#define DEVTOOLS_H

#include <QDockWidget>
#include <QTabWidget>
#include <QTextEdit>
#include <QTreeWidget>
#include <QTableWidget>
#include <QWebEngineView>

class BrowserWindow;

class DevTools : public QDockWidget
{
    Q_OBJECT

public:
    explicit DevTools(BrowserWindow *browser, QWidget *parent = nullptr);
    
    void showConsole();
    void showNetwork();
    void showElements();
    void showApplication();
    void showSecurity();
    void showPageSource();

private slots:
    void onConsoleMessage(const QString &message, int line, const QString &source);
    void onNetworkRequest(const QUrl &url, const QString &method);
    void onNetworkResponse(const QUrl &url, int status, const QString &contentType);

private:
    void setupUI();
    void setupConsole();
    void setupNetwork();
    void setupElements();
    void setupApplication();
    void setupSecurity();
    
    BrowserWindow *m_browser;
    QTabWidget *m_tabs;
    
    // Console
    QTextEdit *m_console;
    
    // Network
    QTableWidget *m_networkTable;
    
    // Elements
    QTreeWidget *m_elementsTree;
    
    // Application
    QTreeWidget *m_applicationTree;
    
    // Security
    QTextEdit *m_securityInfo;
    
    // Page Source
    QTextEdit *m_pageSource;
};

#endif // DEVTOOLS_H
