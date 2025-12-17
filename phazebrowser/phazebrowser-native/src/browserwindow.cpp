#include "browserwindow.h"
#include "privacyengine.h"
#include <QWebEngineSettings>
#include <QWebEngineProfile>
#include <QWebEngineScript>
#include <QWebEngineScriptCollection>
#include <QWebEngineHistory>
#include <QPrintDialog>
#include <QPrinter>
#include <QFile>
#include <QPixmap>
#include <QDebug>
#include <QStandardPaths>
#include <QDesktopServices>

BrowserWindow::BrowserWindow(QWidget *parent)
    : QWidget(parent)
    , privacyEngine(new PrivacyEngine(this))
    , devTools(nullptr)
    , faviconManager(new FaviconManager(this))
    , m_zoomFactor(1.0)
    , m_readerMode(false)
    , m_muted(false)
{
    layout = new QVBoxLayout(this);
    layout->setContentsMargins(0, 0, 0, 0);
    
    // Create WebEngineView
    m_webView = new QWebEngineView(this);
    
    // Enable PDF Viewer support
    QWebEngineSettings *settings = m_webView->settings();
    settings->setAttribute(QWebEngineSettings::PdfViewerEnabled, true);
    
    // Spell checking is enabled by default in Qt6 WebEngine
    
    // Apply privacy settings
    privacyEngine->applyPrivacySettings(m_webView);
    
    // Set user agent
    QWebEngineProfile *profile = m_webView->page()->profile();
    profile->setHttpUserAgent("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) PhazeBrowser/2.0 Chrome/120.0.0.0 Safari/537.36");
    
    // Setup download handler
    connect(profile, &QWebEngineProfile::downloadRequested, [this](QWebEngineDownloadRequest *download) {
        emit downloadRequested(download);
    });
    
    layout->addWidget(m_webView);
    
    // Connect signals
    connect(m_webView, &QWebEngineView::urlChanged, this, &BrowserWindow::onUrlChanged);
    connect(m_webView, &QWebEngineView::titleChanged, this, &BrowserWindow::onTitleChanged);
    connect(m_webView, &QWebEngineView::loadStarted, this, &BrowserWindow::onLoadStarted);
    connect(m_webView, &QWebEngineView::loadFinished, this, &BrowserWindow::onLoadFinished);
    
    // Favicon loading
    connect(faviconManager, &FaviconManager::faviconLoaded, this, &BrowserWindow::onFaviconLoaded);
    
    setupFindInPage();
}

BrowserWindow::~BrowserWindow()
{
    if (devTools) {
        delete devTools;
    }
}

void BrowserWindow::loadUrl(const QUrl &url)
{
    // Allow internal URLs (about:, data:, file:) without VPN check
    QString scheme = url.scheme().toLower();
    if (scheme == "about" || scheme == "data" || scheme == "file" || url.toString().startsWith("about:")) {
        m_webView->load(url);
        faviconManager->loadFavicon(url);
        return;
    }
    
    // For external URLs, VPN check is handled by MainWindow
    m_webView->load(url);
    faviconManager->loadFavicon(url);
}

void BrowserWindow::goBack()
{
    m_webView->back();
}

void BrowserWindow::goForward()
{
    m_webView->forward();
}

void BrowserWindow::reload()
{
    m_webView->reload();
}

bool BrowserWindow::canGoBack() const
{
    return m_webView->history()->canGoBack();
}

bool BrowserWindow::canGoForward() const
{
    return m_webView->history()->canGoForward();
}

QUrl BrowserWindow::url() const
{
    return m_webView->url();
}

QString BrowserWindow::title() const
{
    return m_webView->title();
}

void BrowserWindow::findInPage(const QString &text)
{
    m_webView->findText(text);
}

void BrowserWindow::findNext()
{
    m_webView->findText(m_webView->selectedText(), QWebEnginePage::FindFlags());
}

void BrowserWindow::findPrevious()
{
    m_webView->findText(m_webView->selectedText(), QWebEnginePage::FindBackward);
}

void BrowserWindow::print()
{
    // Qt6 WebEngine uses printToPdf for printing
    QString tempFile = QStandardPaths::writableLocation(QStandardPaths::TempLocation) + "/phazebrowser_print.pdf";
    m_webView->page()->printToPdf([tempFile](const QByteArray &pdfData) {
        QFile file(tempFile);
        if (file.open(QIODevice::WriteOnly)) {
            file.write(pdfData);
            file.close();
            // Open PDF with system default viewer/printer
            QDesktopServices::openUrl(QUrl::fromLocalFile(tempFile));
        }
    });
}

void BrowserWindow::printToPdf(const QString &filename)
{
    m_webView->page()->printToPdf([filename](const QByteArray &pdfData) {
        QFile file(filename);
        if (file.open(QIODevice::WriteOnly)) {
            file.write(pdfData);
        }
    });
}

void BrowserWindow::zoomIn()
{
    setZoomFactor(m_zoomFactor + 0.1);
}

void BrowserWindow::zoomOut()
{
    setZoomFactor(m_zoomFactor - 0.1);
}

void BrowserWindow::zoomReset()
{
    setZoomFactor(1.0);
}

void BrowserWindow::setZoomFactor(double factor)
{
    m_zoomFactor = qBound(0.25, factor, 5.0);
    m_webView->setZoomFactor(m_zoomFactor);
    emit zoomFactorChanged(m_zoomFactor);
}

double BrowserWindow::zoomFactor() const
{
    return m_zoomFactor;
}

void BrowserWindow::toggleFullScreen()
{
    if (isFullScreen()) {
        showNormal();
    } else {
        showFullScreen();
    }
}

void BrowserWindow::showDevTools()
{
    if (!devTools) {
        devTools = new DevTools(this, parentWidget());
    }
    devTools->show();
}

void BrowserWindow::hideDevTools()
{
    if (devTools) {
        devTools->hide();
    }
}

bool BrowserWindow::isDevToolsVisible() const
{
    return devTools && devTools->isVisible();
}

QPixmap BrowserWindow::favicon() const
{
    return currentFavicon;
}

void BrowserWindow::toggleReaderMode()
{
    m_readerMode = !m_readerMode;
    
    if (m_readerMode) {
        // Inject reader mode CSS and JavaScript
        QString readerScript = R"(
            (function() {
                // Remove ads, sidebars, navigation, etc.
                const style = document.createElement('style');
                style.textContent = `
                    body { max-width: 800px; margin: 0 auto; padding: 20px; font-family: Georgia, serif; line-height: 1.6; }
                    nav, aside, .sidebar, .ad, .advertisement, [class*="ad-"], [id*="ad-"],
                    header, footer, .header, .footer, .navigation, .nav,
                    .social-share, .share-buttons, .comments, .comment-section { display: none !important; }
                    article, main, .content, .post, .article { width: 100% !important; max-width: none !important; }
                `;
                document.head.appendChild(style);
            })();
        )";
        
        QWebEngineScript script;
        script.setName("ReaderMode");
        script.setSourceCode(readerScript);
        script.setInjectionPoint(QWebEngineScript::DocumentReady);
        script.setWorldId(QWebEngineScript::MainWorld);
        m_webView->page()->scripts().insert(script);
    } else {
        // Remove reader mode script
        QWebEngineScriptCollection &scripts = m_webView->page()->scripts();
        for (const QWebEngineScript &s : scripts.find("ReaderMode")) {
            scripts.remove(s);
        }
        m_webView->reload();
    }
}

bool BrowserWindow::isReaderMode() const
{
    return m_readerMode;
}

void BrowserWindow::setMuted(bool muted)
{
    m_muted = muted;
    m_webView->page()->setAudioMuted(muted);
}

bool BrowserWindow::isMuted() const
{
    return m_muted;
}

void BrowserWindow::setupFindInPage()
{
    // Find in page is handled by QWebEngineView::findText()
    // We'll add a dialog in MainWindow
}

void BrowserWindow::showVPNWarning()
{
    QString warningHtml = R"(
        <!DOCTYPE html>
        <html>
        <head>
            <title>VPN Required - PhazeBrowser</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    text-align: center;
                }
                .container {
                    background: rgba(0,0,0,0.3);
                    padding: 40px;
                    border-radius: 20px;
                    max-width: 600px;
                }
                h1 { font-size: 48px; margin: 0 0 20px 0; }
                p { font-size: 18px; line-height: 1.6; }
                .icon { font-size: 80px; margin-bottom: 20px; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🔒</div>
                <h1>VPN Required</h1>
                <p>PhazeBrowser requires an active VPN connection to protect your privacy.</p>
                <p>Please connect to your VPN and refresh this page.</p>
                <p><strong>Your browsing is blocked until VPN is connected.</strong></p>
            </div>
        </body>
        </html>
    )";
    
    // Use setHtml with a proper base URL so the URL bar shows correctly
    QUrl baseUrl("about:vpn-required");
    m_webView->setHtml(warningHtml, baseUrl);
}

void BrowserWindow::onUrlChanged(const QUrl &url)
{
    emit urlChanged(url);
    // Only load favicon for real URLs, not internal pages
    if (url.scheme() != "about" && url.scheme() != "data") {
        faviconManager->loadFavicon(url);
    }
}

void BrowserWindow::onTitleChanged(const QString &title)
{
    emit titleChanged(title);
}

void BrowserWindow::onLoadStarted()
{
    emit loadStarted();
}

void BrowserWindow::onLoadFinished(bool success)
{
    emit loadFinished(success);
}

void BrowserWindow::onFaviconLoaded(const QUrl &url, const QPixmap &favicon)
{
    if (m_webView->url().host() == url.host()) {
        currentFavicon = favicon;
        emit faviconChanged(favicon);
    }
}
