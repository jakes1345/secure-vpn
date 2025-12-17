#ifndef MAINWINDOW_H
#define MAINWINDOW_H

#include <QMainWindow>
#include <QTabWidget>
#include <QTabBar>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QPushButton>
#include <QLineEdit>
#include <QLabel>
#include <QStatusBar>
#include <QCompleter>
#include <QStringListModel>
#include <QWebEngineDownloadRequest>

// Forward declarations
class BrowserWindow;
class VPNManager;
class DataManager;
class PrivacyEngine;
class DownloadManager;
class SearchManager;
class FaviconManager;

class MainWindow : public QMainWindow
{
    Q_OBJECT

public:
    explicit MainWindow(QWidget *parent = nullptr);
    ~MainWindow();

private slots:
    void onNewTab();
    void onCloseTab(int index);
    void onTabChanged(int index);
    void onBackClicked();
    void onForwardClicked();
    void onReloadClicked();
    void onUrlEntered();
    void onVPNConnect();
    void onVPNDisconnect();
    void onVPNStatusChanged(bool connected);
    void onVPNDialog();
    void onBookmarks();
    void onHistory();
    void onSettings();
    void onPrivacyDashboard();
    void onPasswordManager();
    void onDownloads();
    void onFindInPage();
    void onPrint();
    void onZoomIn();
    void onZoomOut();
    void onZoomReset();
    void onFullScreen();
    void onDevTools();
    void onReaderMode();
    void onBrowserUrlChanged(const QUrl &url);
    void onBrowserTitleChanged(const QString &title);
    void onBrowserLoadFinished(bool success);
    void onBrowserFaviconChanged(const QPixmap &favicon);
    void onDownloadRequested(QWebEngineDownloadRequest *download);
    void onTabContextMenu(const QPoint &pos);
    void onPinTab(int index);
    void onUnpinTab(int index);
    void onMuteTab(int index);
    void onUnmuteTab(int index);
    void onDuplicateTab(int index);

private:
    void setupUI();
    void setupVPN();
    void updateVPNStatus();
    BrowserWindow* currentBrowser();
    void saveSession();
    void restoreSession();
    
    QWidget *centralWidget;
    QVBoxLayout *mainLayout;
    QHBoxLayout *toolbarLayout;
    
    // Navigation
    QPushButton *backBtn;
    QPushButton *forwardBtn;
    QPushButton *reloadBtn;
    QLineEdit *urlBar;
    QPushButton *vpnBtn;
    QPushButton *bookmarksBtn;
    QPushButton *historyBtn;
    QPushButton *settingsBtn;
    
    // VPN Status
    QLabel *vpnStatusLabel;
    
    // Tabs
    QTabWidget *tabWidget;
    
    // Managers
    VPNManager *vpnManager;
    DataManager *dataManager;
    DownloadManager *downloadManager;
    SearchManager *searchManager;
    FaviconManager *faviconManager;
    
    // Find in Page
    QDialog *findDialog;
    QLineEdit *findInput;
    QPushButton *findNextBtn;
    QPushButton *findPrevBtn;
    
    // Zoom
    QLabel *zoomLabel;
    
    // Autocomplete
    QCompleter *urlCompleter;
    QStringListModel *completerModel;
    void setupAutocomplete();
    void updateAutocomplete();
};

#endif // MAINWINDOW_H
