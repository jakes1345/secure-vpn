#include "mainwindow.h"
#include "browserwindow.h"
#include "vpnmanager.h"
#include "datamanager.h"
#include "privacyengine.h"
#include "downloadmanager.h"
#include "searchmanager.h"
#include "faviconmanager.h"
#include "downloaddialog.h"
#include "settingsdialog.h"
#include "privacydashboard.h"
#include "passworddialog.h"
#include "bookmarksdialog.h"
#include "historydialog.h"
#include <QMessageBox>
#include <QInputDialog>
#include <QFileDialog>
#include <QDir>
#include <QStandardPaths>
#include <QMenu>
#include <QAction>
#include <QDialog>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QKeySequence>
#include <QShortcut>
#include <QJsonArray>
#include <QJsonObject>
#include <QJsonValue>
#include <QCompleter>
#include <QStringListModel>
#include <QPoint>
#include <QIcon>

MainWindow::MainWindow(QWidget *parent)
    : QMainWindow(parent)
    , vpnManager(new VPNManager(this))
    , dataManager(new DataManager(this))
    , downloadManager(new DownloadManager(this))
    , searchManager(new SearchManager(this))
    , faviconManager(new FaviconManager(this))
    , findDialog(nullptr)
{
    setupUI();
    setupVPN();
    
    // Restore session or create first tab
    restoreSession();
    
    // Check VPN status
    updateVPNStatus();
}

MainWindow::~MainWindow()
{
    // Save session before closing
    saveSession();
}

void MainWindow::setupUI()
{
    centralWidget = new QWidget(this);
    setCentralWidget(centralWidget);
    
    mainLayout = new QVBoxLayout(centralWidget);
    mainLayout->setContentsMargins(0, 0, 0, 0);
    mainLayout->setSpacing(0);
    
    // Toolbar
    toolbarLayout = new QHBoxLayout();
    toolbarLayout->setContentsMargins(8, 8, 8, 8);
    toolbarLayout->setSpacing(8);
    
    // VPN Status
    vpnStatusLabel = new QLabel("🔴 VPN Disconnected", this);
    vpnStatusLabel->setStyleSheet("padding: 4px 12px; background: #3d3d3d; border-radius: 4px;");
    toolbarLayout->addWidget(vpnStatusLabel);
    
    // Navigation buttons
    backBtn = new QPushButton("←", this);
    backBtn->setFixedSize(32, 32);
    backBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(backBtn, &QPushButton::clicked, this, &MainWindow::onBackClicked);
    toolbarLayout->addWidget(backBtn);
    
    forwardBtn = new QPushButton("→", this);
    forwardBtn->setFixedSize(32, 32);
    forwardBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(forwardBtn, &QPushButton::clicked, this, &MainWindow::onForwardClicked);
    toolbarLayout->addWidget(forwardBtn);
    
    reloadBtn = new QPushButton("↻", this);
    reloadBtn->setFixedSize(32, 32);
    reloadBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(reloadBtn, &QPushButton::clicked, this, &MainWindow::onReloadClicked);
    toolbarLayout->addWidget(reloadBtn);
    
    // URL Bar with autocomplete
    urlBar = new QLineEdit(this);
    urlBar->setPlaceholderText("Enter URL or search...");
    urlBar->setStyleSheet("QLineEdit { padding: 6px 12px; background: #3d3d3d; border: 1px solid #404040; border-radius: 4px; } QLineEdit:focus { border-color: #0078d4; }");
    connect(urlBar, &QLineEdit::returnPressed, this, &MainWindow::onUrlEntered);
    
    // Setup autocomplete
    setupAutocomplete();
    
    toolbarLayout->addWidget(urlBar, 1);
    
    // VPN Button
    vpnBtn = new QPushButton("🔌 Connect VPN", this);
    vpnBtn->setStyleSheet("QPushButton { padding: 6px 12px; background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(vpnBtn, &QPushButton::clicked, this, &MainWindow::onVPNDialog);
    toolbarLayout->addWidget(vpnBtn);
    
    // Bookmarks Button
    bookmarksBtn = new QPushButton("⭐", this);
    bookmarksBtn->setFixedSize(32, 32);
    bookmarksBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(bookmarksBtn, &QPushButton::clicked, this, &MainWindow::onBookmarks);
    toolbarLayout->addWidget(bookmarksBtn);
    
    // History Button
    historyBtn = new QPushButton("🕐", this);
    historyBtn->setFixedSize(32, 32);
    historyBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(historyBtn, &QPushButton::clicked, this, &MainWindow::onHistory);
    toolbarLayout->addWidget(historyBtn);
    
    // Downloads Button
    QPushButton *downloadsBtn = new QPushButton("⬇️", this);
    downloadsBtn->setFixedSize(32, 32);
    downloadsBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(downloadsBtn, &QPushButton::clicked, this, &MainWindow::onDownloads);
    toolbarLayout->addWidget(downloadsBtn);
    
    // Find Button
    QPushButton *findBtn = new QPushButton("🔍", this);
    findBtn->setFixedSize(32, 32);
    findBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(findBtn, &QPushButton::clicked, this, &MainWindow::onFindInPage);
    toolbarLayout->addWidget(findBtn);
    
    // Zoom Label
    zoomLabel = new QLabel("100%", this);
    zoomLabel->setStyleSheet("padding: 4px 8px; background: #3d3d3d; border-radius: 4px; font-size: 12px;");
    toolbarLayout->addWidget(zoomLabel);
    
    // Zoom Controls
    QPushButton *zoomOutBtn = new QPushButton("−", this);
    zoomOutBtn->setFixedSize(24, 24);
    zoomOutBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(zoomOutBtn, &QPushButton::clicked, this, &MainWindow::onZoomOut);
    toolbarLayout->addWidget(zoomOutBtn);
    
    QPushButton *zoomInBtn = new QPushButton("+", this);
    zoomInBtn->setFixedSize(24, 24);
    zoomInBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(zoomInBtn, &QPushButton::clicked, this, &MainWindow::onZoomIn);
    toolbarLayout->addWidget(zoomInBtn);
    
    // Settings Button
    settingsBtn = new QPushButton("⚙️", this);
    settingsBtn->setFixedSize(32, 32);
    settingsBtn->setStyleSheet("QPushButton { background: #3d3d3d; border: none; border-radius: 4px; } QPushButton:hover { background: #4d4d4d; }");
    connect(settingsBtn, &QPushButton::clicked, this, &MainWindow::onSettings);
    toolbarLayout->addWidget(settingsBtn);
    
    mainLayout->addLayout(toolbarLayout);
    
    // Tab Widget
    tabWidget = new QTabWidget(this);
    tabWidget->setTabsClosable(true);
    tabWidget->setMovable(true);
    tabWidget->setStyleSheet("QTabWidget::pane { border: none; background: #1e1e1e; } QTabBar::tab { background: #2d2d2d; color: white; padding: 8px 16px; } QTabBar::tab:selected { background: #1e1e1e; border-bottom: 2px solid #0078d4; }");
    connect(tabWidget, &QTabWidget::tabCloseRequested, this, &MainWindow::onCloseTab);
    connect(tabWidget, &QTabWidget::currentChanged, this, &MainWindow::onTabChanged);
    connect(tabWidget, &QTabWidget::tabBarDoubleClicked, this, &MainWindow::onNewTab);
    mainLayout->addWidget(tabWidget);
    
    // Status Bar
    statusBar()->showMessage("Ready");
    
    // Keyboard shortcuts
    QShortcut *findShortcut = new QShortcut(QKeySequence::Find, this);
    connect(findShortcut, &QShortcut::activated, this, &MainWindow::onFindInPage);
    
    QShortcut *printShortcut = new QShortcut(QKeySequence::Print, this);
    connect(printShortcut, &QShortcut::activated, this, &MainWindow::onPrint);
    
    QShortcut *zoomInShortcut = new QShortcut(QKeySequence::ZoomIn, this);
    connect(zoomInShortcut, &QShortcut::activated, this, &MainWindow::onZoomIn);
    
    QShortcut *zoomOutShortcut = new QShortcut(QKeySequence::ZoomOut, this);
    connect(zoomOutShortcut, &QShortcut::activated, this, &MainWindow::onZoomOut);
    
    QShortcut *devToolsShortcut = new QShortcut(Qt::CTRL | Qt::SHIFT | Qt::Key_I, this);
    connect(devToolsShortcut, &QShortcut::activated, this, &MainWindow::onDevTools);
    
    QShortcut *newTabShortcut = new QShortcut(Qt::CTRL | Qt::Key_T, this);
    connect(newTabShortcut, &QShortcut::activated, this, &MainWindow::onNewTab);
    
    // Tab context menu for pinning/muting
    tabWidget->setContextMenuPolicy(Qt::CustomContextMenu);
    connect(tabWidget, &QTabWidget::customContextMenuRequested, this, &MainWindow::onTabContextMenu);
}

void MainWindow::setupAutocomplete()
{
    completerModel = new QStringListModel(this);
    urlCompleter = new QCompleter(completerModel, this);
    urlCompleter->setCaseSensitivity(Qt::CaseInsensitive);
    urlCompleter->setCompletionMode(QCompleter::PopupCompletion);
    urlCompleter->setFilterMode(Qt::MatchContains);
    urlBar->setCompleter(urlCompleter);
    updateAutocomplete();
}

void MainWindow::updateAutocomplete()
{
    QStringList suggestions;
    
    // Add history URLs
    QJsonArray history = dataManager->getHistory();
    for (const QJsonValue &value : history) {
        QJsonObject entry = value.toObject();
        QString url = entry["url"].toString();
        QString title = entry["title"].toString();
        if (!url.isEmpty()) {
            suggestions << url;
            if (!title.isEmpty()) {
                suggestions << title;
            }
        }
    }
    
    // Add bookmarks
    QJsonArray bookmarks = dataManager->getBookmarks();
    for (const QJsonValue &value : bookmarks) {
        QJsonObject bookmark = value.toObject();
        QString url = bookmark["url"].toString();
        QString title = bookmark["title"].toString();
        if (!url.isEmpty()) {
            suggestions << url;
            if (!title.isEmpty()) {
                suggestions << title;
            }
        }
    }
    
    // Remove duplicates and sort
    suggestions.removeDuplicates();
    suggestions.sort();
    
    completerModel->setStringList(suggestions);
}

void MainWindow::setupVPN()
{
    connect(vpnManager, &VPNManager::statusChanged, this, &MainWindow::onVPNStatusChanged);
}

void MainWindow::onNewTab()
{
    BrowserWindow *browser = new BrowserWindow(this);
    int index = tabWidget->addTab(browser, "New Tab");
    tabWidget->setCurrentIndex(index);
    
    connect(browser, &BrowserWindow::urlChanged, [this, browser](const QUrl &url) {
        int index = tabWidget->indexOf(browser);
        if (index >= 0) {
            tabWidget->setTabText(index, browser->title().isEmpty() ? "New Tab" : browser->title());
            if (tabWidget->currentIndex() == index) {
                urlBar->setText(url.toString());
            }
        }
    });
    
    connect(browser, &BrowserWindow::titleChanged, [this, browser](const QString &title) {
        int index = tabWidget->indexOf(browser);
        if (index >= 0) {
            tabWidget->setTabText(index, title.isEmpty() ? "New Tab" : title);
        }
    });
    
    connect(browser, &BrowserWindow::loadStarted, [this]() {
        reloadBtn->setText("⏸");
    });
    
    connect(browser, &BrowserWindow::loadFinished, [this]() {
        reloadBtn->setText("↻");
    });
    
    connect(browser, &BrowserWindow::urlChanged, this, &MainWindow::onBrowserUrlChanged);
    connect(browser, &BrowserWindow::titleChanged, this, &MainWindow::onBrowserTitleChanged);
    connect(browser, &BrowserWindow::loadFinished, this, &MainWindow::onBrowserLoadFinished);
    connect(browser, &BrowserWindow::faviconChanged, this, &MainWindow::onBrowserFaviconChanged);
    connect(browser, &BrowserWindow::downloadRequested, this, &MainWindow::onDownloadRequested);
    connect(browser, &BrowserWindow::zoomFactorChanged, [this](double factor) {
        zoomLabel->setText(QString::number(static_cast<int>(factor * 100)) + "%");
    });
    
    // Load default page or show VPN warning
    if (vpnManager->isConnected()) {
        browser->loadUrl(QUrl("https://phazevpn.com"));
    } else {
        browser->showVPNWarning();
    }
}

void MainWindow::onCloseTab(int index)
{
    if (tabWidget->count() <= 1) {
        return; // Don't close last tab
    }
    
    QWidget *widget = tabWidget->widget(index);
    tabWidget->removeTab(index);
    widget->deleteLater();
    
    // Save session after closing tab
    saveSession();
}

void MainWindow::onTabChanged(int index)
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        urlBar->setText(browser->url().toString());
        backBtn->setEnabled(browser->canGoBack());
        forwardBtn->setEnabled(browser->canGoForward());
    }
}

void MainWindow::onBackClicked()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        browser->goBack();
    }
}

void MainWindow::onForwardClicked()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        browser->goForward();
    }
}

void MainWindow::onReloadClicked()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        browser->reload();
    }
}

void MainWindow::onUrlEntered()
{
    QString urlText = urlBar->text().trimmed();
    if (urlText.isEmpty()) return;
    
    BrowserWindow *browser = currentBrowser();
    if (!browser) return;
    
    QUrl url;
    if (urlText.contains('.') && !urlText.contains(' ')) {
        // Looks like a URL
        if (!urlText.startsWith("http://") && !urlText.startsWith("https://") && 
            !urlText.startsWith("about:") && !urlText.startsWith("data:")) {
            url = QUrl("https://" + urlText);
        } else {
            url = QUrl(urlText);
        }
    } else {
        // Search query - use search manager
        url = searchManager->searchUrl(urlText);
    }
    
    // Check VPN status for external URLs
    QString scheme = url.scheme().toLower();
    if ((scheme == "http" || scheme == "https") && !vpnManager->isConnected()) {
        browser->showVPNWarning();
        urlBar->setText("about:vpn-required");
        return;
    }
    
    browser->loadUrl(url);
}

void MainWindow::onVPNDialog()
{
    if (vpnManager->isConnected()) {
        int ret = QMessageBox::question(this, "Disconnect VPN", "Are you sure you want to disconnect from VPN?");
        if (ret == QMessageBox::Yes) {
            vpnManager->disconnectVPN();
        }
        return;
    }
    
    // Show VPN config selection dialog
    QString downloadsPath = QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
    QString configFile = QFileDialog::getOpenFileName(this, "Select VPN Config", downloadsPath, "VPN Configs (*.ovpn *.conf)");
    
    if (!configFile.isEmpty()) {
        QString protocol = configFile.endsWith(".ovpn") ? "openvpn" : "wireguard";
        vpnManager->connectVPN(configFile, protocol);
    }
}

void MainWindow::onVPNConnect()
{
    // Show VPN config selection dialog
    QString downloadsPath = QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
    QString configFile = QFileDialog::getOpenFileName(this, "Select VPN Config", downloadsPath, "VPN Configs (*.ovpn *.conf)");
    
    if (!configFile.isEmpty()) {
        QString protocol = configFile.endsWith(".ovpn") ? "openvpn" : "wireguard";
        vpnManager->connectVPN(configFile, protocol);
    }
}

void MainWindow::onVPNDisconnect()
{
    int ret = QMessageBox::question(this, "Disconnect VPN", "Are you sure you want to disconnect from VPN?");
    if (ret == QMessageBox::Yes) {
        vpnManager->disconnectVPN();
    }
}

void MainWindow::onVPNStatusChanged(bool connected)
{
    updateVPNStatus();
}

void MainWindow::updateVPNStatus()
{
    bool connected = vpnManager->isConnected();
    
    if (connected) {
        vpnStatusLabel->setText("🟢 VPN Connected");
        vpnStatusLabel->setStyleSheet("padding: 4px 12px; background: #0078d4; border-radius: 4px;");
        vpnBtn->setText("🔴 Disconnect VPN");
        
        // If current tab is showing VPN warning, load default page
        BrowserWindow *browser = currentBrowser();
        if (browser && browser->url().toString() == "about:vpn-required") {
            browser->loadUrl(QUrl("https://phazevpn.com"));
        }
    } else {
        vpnStatusLabel->setText("🔴 VPN Disconnected");
        vpnStatusLabel->setStyleSheet("padding: 4px 12px; background: #3d3d3d; border-radius: 4px;");
        vpnBtn->setText("🔌 Connect VPN");
        
        // Show warning in current tab
        BrowserWindow *browser = currentBrowser();
        if (browser) {
            browser->showVPNWarning();
            urlBar->setText("about:vpn-required");
        }
    }
}

BrowserWindow* MainWindow::currentBrowser()
{
    return qobject_cast<BrowserWindow*>(tabWidget->currentWidget());
}

void MainWindow::onBookmarks()
{
    QMenu menu(this);
    QJsonArray bookmarks = dataManager->getBookmarks();
    
    if (bookmarks.isEmpty()) {
        QAction *noBookmarks = menu.addAction("No bookmarks yet");
        noBookmarks->setEnabled(false);
    } else {
        for (int i = 0; i < qMin(20, bookmarks.size()); i++) {
            QJsonObject bookmark = bookmarks.at(i).toObject();
            QString title = bookmark["title"].toString();
            QString url = bookmark["url"].toString();
            QAction *action = menu.addAction(title.isEmpty() ? url : title);
            connect(action, &QAction::triggered, [this, url]() {
                BrowserWindow *browser = currentBrowser();
                if (browser) {
                    browser->loadUrl(QUrl(url));
                }
            });
        }
        menu.addSeparator();
        QAction *addCurrent = menu.addAction("Add Current Page");
        connect(addCurrent, &QAction::triggered, [this]() {
            BrowserWindow *browser = currentBrowser();
            if (browser) {
                QString url = browser->url().toString();
                QString title = browser->title();
                dataManager->addBookmark(url, title);
            }
        });
    }
    
    menu.exec(bookmarksBtn->mapToGlobal(QPoint(0, bookmarksBtn->height())));
}

void MainWindow::onHistory()
{
    HistoryDialog *dialog = new HistoryDialog(dataManager, this);
    connect(dialog, &HistoryDialog::urlSelected, [this](const QUrl &url) {
        BrowserWindow *browser = currentBrowser();
        if (browser) {
            browser->loadUrl(url);
        }
    });
    dialog->exec();
    dialog->deleteLater();
}

void MainWindow::onSettings()
{
    BrowserWindow *browser = currentBrowser();
    PrivacyEngine *privacy = browser ? browser->privacy() : nullptr;
    
    SettingsDialog *dialog = new SettingsDialog(dataManager, privacy, searchManager, this);
    dialog->exec();
    dialog->deleteLater();
}

void MainWindow::onPrivacyDashboard()
{
    BrowserWindow *browser = currentBrowser();
    if (browser && browser->privacy()) {
        PrivacyDashboard *dialog = new PrivacyDashboard(browser->privacy(), this);
        dialog->exec();
        dialog->deleteLater();
    }
}

void MainWindow::onBrowserUrlChanged(const QUrl &url)
{
    if (tabWidget->currentWidget() == sender()) {
        urlBar->setText(url.toString());
    }
}

void MainWindow::onBrowserTitleChanged(const QString &title)
{
    BrowserWindow *browser = qobject_cast<BrowserWindow*>(sender());
    if (browser) {
        int index = tabWidget->indexOf(browser);
        if (index >= 0) {
            tabWidget->setTabText(index, title.isEmpty() ? "New Tab" : title.left(25));
        }
    }
}

void MainWindow::onBrowserLoadFinished(bool success)
{
    BrowserWindow *browser = qobject_cast<BrowserWindow*>(sender());
    if (browser && success) {
        // Save to history
        QString url = browser->url().toString();
        QString title = browser->title();
        dataManager->addHistory(url, title);
        
        // Update autocomplete
        updateAutocomplete();
    }
}

void MainWindow::onBrowserFaviconChanged(const QPixmap &favicon)
{
    BrowserWindow *browser = qobject_cast<BrowserWindow*>(sender());
    if (browser) {
        int index = tabWidget->indexOf(browser);
        if (index >= 0 && !favicon.isNull()) {
            tabWidget->setTabIcon(index, QIcon(favicon));
        }
    }
}

void MainWindow::onDownloadRequested(QWebEngineDownloadRequest *download)
{
    downloadManager->addDownload(download);
}

void MainWindow::onDownloads()
{
    DownloadDialog *dialog = new DownloadDialog(downloadManager, this);
    dialog->exec();
    dialog->deleteLater();
}

void MainWindow::onFindInPage()
{
    if (!findDialog) {
        findDialog = new QDialog(this);
        findDialog->setWindowTitle("Find in Page");
        findDialog->setFixedSize(400, 100);
        
        QVBoxLayout *layout = new QVBoxLayout(findDialog);
        QHBoxLayout *inputLayout = new QHBoxLayout();
        
        findInput = new QLineEdit(findDialog);
        findInput->setPlaceholderText("Find in page...");
        inputLayout->addWidget(findInput);
        
        findNextBtn = new QPushButton("Next", findDialog);
        findPrevBtn = new QPushButton("Previous", findDialog);
        inputLayout->addWidget(findPrevBtn);
        inputLayout->addWidget(findNextBtn);
        
        layout->addLayout(inputLayout);
        
        connect(findInput, &QLineEdit::textChanged, [this](const QString &text) {
            BrowserWindow *browser = currentBrowser();
            if (browser) {
                browser->findInPage(text);
            }
        });
        
        connect(findNextBtn, &QPushButton::clicked, [this]() {
            BrowserWindow *browser = currentBrowser();
            if (browser) {
                browser->findNext();
            }
        });
        
        connect(findPrevBtn, &QPushButton::clicked, [this]() {
            BrowserWindow *browser = currentBrowser();
            if (browser) {
                browser->findPrevious();
            }
        });
    }
    
    findDialog->show();
    findInput->setFocus();
    findInput->selectAll();
}

void MainWindow::onPrint()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        browser->print();
    }
}

void MainWindow::onZoomIn()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        browser->zoomIn();
    }
}

void MainWindow::onZoomOut()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        browser->zoomOut();
    }
}

void MainWindow::onZoomReset()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        browser->zoomReset();
    }
}

void MainWindow::onFullScreen()
{
    if (isFullScreen()) {
        showNormal();
    } else {
        showFullScreen();
    }
}

void MainWindow::onDevTools()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        if (browser->isDevToolsVisible()) {
            browser->hideDevTools();
        } else {
            browser->showDevTools();
        }
    }
}

void MainWindow::onReaderMode()
{
    BrowserWindow *browser = currentBrowser();
    if (browser) {
        browser->toggleReaderMode();
    }
}

void MainWindow::onPasswordManager()
{
    PasswordDialog *dialog = new PasswordDialog(dataManager, this);
    dialog->exec();
    dialog->deleteLater();
}

void MainWindow::saveSession()
{
    QJsonArray session;
    for (int i = 0; i < tabWidget->count(); ++i) {
        BrowserWindow *browser = qobject_cast<BrowserWindow*>(tabWidget->widget(i));
        if (browser) {
            QJsonObject tab;
            tab["url"] = browser->url().toString();
            tab["title"] = browser->title();
            tab["pinned"] = tabWidget->tabBar()->tabData(i).toBool();
            session.append(tab);
        }
    }
    dataManager->setSession(session);
}

void MainWindow::restoreSession()
{
    QJsonArray session = dataManager->getSession();
    
    if (session.isEmpty()) {
        // No saved session, create first tab
        onNewTab();
        return;
    }
    
    // Restore tabs from session
    for (const QJsonValue &value : session) {
        QJsonObject tab = value.toObject();
        QString url = tab["url"].toString();
        QString title = tab["title"].toString();
        bool pinned = tab["pinned"].toBool();
        
        BrowserWindow *browser = new BrowserWindow(this);
        int index = tabWidget->addTab(browser, title.isEmpty() ? "New Tab" : title);
        
        if (pinned) {
            tabWidget->tabBar()->setTabData(index, true);
            // Visual indicator for pinned tabs (smaller width)
            tabWidget->setTabIcon(index, QIcon("🔒"));
        }
        
        // Connect signals
        connect(browser, &BrowserWindow::urlChanged, [this, browser](const QUrl &url) {
            int index = tabWidget->indexOf(browser);
            if (index >= 0) {
                tabWidget->setTabText(index, browser->title().isEmpty() ? "New Tab" : browser->title());
                if (tabWidget->currentIndex() == index) {
                    urlBar->setText(url.toString());
                }
            }
        });
        
        connect(browser, &BrowserWindow::titleChanged, [this, browser](const QString &title) {
            int index = tabWidget->indexOf(browser);
            if (index >= 0) {
                tabWidget->setTabText(index, title.isEmpty() ? "New Tab" : title);
            }
        });
        
        connect(browser, &BrowserWindow::loadStarted, [this]() {
            reloadBtn->setText("⏸");
        });
        
        connect(browser, &BrowserWindow::loadFinished, [this]() {
            reloadBtn->setText("↻");
        });
        
        connect(browser, &BrowserWindow::urlChanged, this, &MainWindow::onBrowserUrlChanged);
        connect(browser, &BrowserWindow::titleChanged, this, &MainWindow::onBrowserTitleChanged);
        connect(browser, &BrowserWindow::loadFinished, this, &MainWindow::onBrowserLoadFinished);
        connect(browser, &BrowserWindow::faviconChanged, this, &MainWindow::onBrowserFaviconChanged);
        connect(browser, &BrowserWindow::downloadRequested, this, &MainWindow::onDownloadRequested);
        connect(browser, &BrowserWindow::zoomFactorChanged, [this](double factor) {
            zoomLabel->setText(QString::number(static_cast<int>(factor * 100)) + "%");
        });
        
        // Load URL or show VPN warning
        if (!url.isEmpty() && url != "about:vpn-required") {
            QString scheme = QUrl(url).scheme().toLower();
            if ((scheme == "http" || scheme == "https") && !vpnManager->isConnected()) {
                browser->showVPNWarning();
            } else {
                browser->loadUrl(QUrl(url));
            }
        } else if (vpnManager->isConnected()) {
            browser->loadUrl(QUrl("https://phazevpn.com"));
        } else {
            browser->showVPNWarning();
        }
    }
    
    // Set first tab as current
    if (tabWidget->count() > 0) {
        tabWidget->setCurrentIndex(0);
    }
}

void MainWindow::onTabContextMenu(const QPoint &pos)
{
    int index = tabWidget->tabBar()->tabAt(pos);
    if (index < 0) return;
    
    QMenu menu(this);
    bool pinned = tabWidget->tabBar()->tabData(index).toBool();
    
    if (pinned) {
        QAction *unpinAction = menu.addAction("Unpin Tab");
        connect(unpinAction, &QAction::triggered, [this, index]() { onUnpinTab(index); });
    } else {
        QAction *pinAction = menu.addAction("Pin Tab");
        connect(pinAction, &QAction::triggered, [this, index]() { onPinTab(index); });
    }
    
    BrowserWindow *browser = qobject_cast<BrowserWindow*>(tabWidget->widget(index));
    if (browser) {
        bool muted = browser->isMuted();
        if (muted) {
            QAction *unmuteAction = menu.addAction("Unmute Tab");
            connect(unmuteAction, &QAction::triggered, [this, index]() { onUnmuteTab(index); });
        } else {
            QAction *muteAction = menu.addAction("Mute Tab");
            connect(muteAction, &QAction::triggered, [this, index]() { onMuteTab(index); });
        }
        
        QAction *duplicateAction = menu.addAction("Duplicate Tab");
        connect(duplicateAction, &QAction::triggered, [this, index]() { onDuplicateTab(index); });
    }
    
    menu.addSeparator();
    QAction *closeAction = menu.addAction("Close Tab");
    connect(closeAction, &QAction::triggered, [this, index]() { onCloseTab(index); });
    
    menu.exec(tabWidget->tabBar()->mapToGlobal(pos));
}

void MainWindow::onPinTab(int index)
{
    tabWidget->tabBar()->setTabData(index, true);
    BrowserWindow *browser = qobject_cast<BrowserWindow*>(tabWidget->widget(index));
    if (browser) {
        QString title = browser->title();
        if (title.isEmpty()) title = "New Tab";
        tabWidget->setTabText(index, "📌 " + title);
    }
    saveSession();
}

void MainWindow::onUnpinTab(int index)
{
    tabWidget->tabBar()->setTabData(index, false);
    BrowserWindow *browser = qobject_cast<BrowserWindow*>(tabWidget->widget(index));
    if (browser) {
        QString title = browser->title();
        if (title.isEmpty()) title = "New Tab";
        tabWidget->setTabText(index, title);
    }
    saveSession();
}

void MainWindow::onMuteTab(int index)
{
    BrowserWindow *browser = qobject_cast<BrowserWindow*>(tabWidget->widget(index));
    if (browser) {
        browser->setMuted(true);
        QString title = browser->title();
        if (title.isEmpty()) title = "New Tab";
        tabWidget->setTabText(index, "🔇 " + title);
    }
}

void MainWindow::onUnmuteTab(int index)
{
    BrowserWindow *browser = qobject_cast<BrowserWindow*>(tabWidget->widget(index));
    if (browser) {
        browser->setMuted(false);
        QString title = browser->title();
        if (title.isEmpty()) title = "New Tab";
        bool pinned = tabWidget->tabBar()->tabData(index).toBool();
        tabWidget->setTabText(index, pinned ? "📌 " + title : title);
    }
}

void MainWindow::onDuplicateTab(int index)
{
    BrowserWindow *sourceBrowser = qobject_cast<BrowserWindow*>(tabWidget->widget(index));
    if (!sourceBrowser) return;
    
    BrowserWindow *newBrowser = new BrowserWindow(this);
    int newIndex = tabWidget->addTab(newBrowser, "New Tab");
    tabWidget->setCurrentIndex(newIndex);
    
    // Copy URL from source tab
    newBrowser->loadUrl(sourceBrowser->url());
    
    // Connect signals (same as onNewTab)
    connect(newBrowser, &BrowserWindow::urlChanged, [this, newBrowser](const QUrl &url) {
        int idx = tabWidget->indexOf(newBrowser);
        if (idx >= 0) {
            tabWidget->setTabText(idx, newBrowser->title().isEmpty() ? "New Tab" : newBrowser->title());
            if (tabWidget->currentIndex() == idx) {
                urlBar->setText(url.toString());
            }
        }
    });
    
    connect(newBrowser, &BrowserWindow::titleChanged, [this, newBrowser](const QString &title) {
        int idx = tabWidget->indexOf(newBrowser);
        if (idx >= 0) {
            tabWidget->setTabText(idx, title.isEmpty() ? "New Tab" : title);
        }
    });
    
    connect(newBrowser, &BrowserWindow::loadStarted, [this]() {
        reloadBtn->setText("⏸");
    });
    
    connect(newBrowser, &BrowserWindow::loadFinished, [this]() {
        reloadBtn->setText("↻");
    });
    
    connect(newBrowser, &BrowserWindow::urlChanged, this, &MainWindow::onBrowserUrlChanged);
    connect(newBrowser, &BrowserWindow::titleChanged, this, &MainWindow::onBrowserTitleChanged);
    connect(newBrowser, &BrowserWindow::loadFinished, this, &MainWindow::onBrowserLoadFinished);
    connect(newBrowser, &BrowserWindow::faviconChanged, this, &MainWindow::onBrowserFaviconChanged);
    connect(newBrowser, &BrowserWindow::downloadRequested, this, &MainWindow::onDownloadRequested);
    connect(newBrowser, &BrowserWindow::zoomFactorChanged, [this](double factor) {
        zoomLabel->setText(QString::number(static_cast<int>(factor * 100)) + "%");
    });
    
    saveSession();
}
