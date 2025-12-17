#ifndef BROWSERWINDOW_H
#define BROWSERWINDOW_H

#include <QWidget>
#include <QVBoxLayout>
#include <QWebEngineView>
#include <QWebEngineDownloadRequest>
#include <QUrl>
#include <QPixmap>
#include "privacyengine.h"
#include "devtools.h"
#include "faviconmanager.h"

class BrowserWindow : public QWidget
{
    Q_OBJECT

public:
    explicit BrowserWindow(QWidget *parent = nullptr);
    ~BrowserWindow();
    
    void loadUrl(const QUrl &url);
    void goBack();
    void goForward();
    void reload();
    bool canGoBack() const;
    bool canGoForward() const;
    QUrl url() const;
    QString title() const;
    void showVPNWarning();
    PrivacyEngine* privacy() const { return privacyEngine; }
    QWebEngineView* webView() const { return m_webView; }
    
    // New features
    void findInPage(const QString &text);
    void findNext();
    void findPrevious();
    void print();
    void printToPdf(const QString &filename);
    void zoomIn();
    void zoomOut();
    void zoomReset();
    void setZoomFactor(double factor);
    double zoomFactor() const;
    void toggleFullScreen();
    void showDevTools();
    void hideDevTools();
    bool isDevToolsVisible() const;
    QPixmap favicon() const;
    void toggleReaderMode();
    bool isReaderMode() const;
    void setMuted(bool muted);
    bool isMuted() const;

signals:
    void urlChanged(const QUrl &url);
    void titleChanged(const QString &title);
    void loadStarted();
    void loadFinished(bool success);
    void faviconChanged(const QPixmap &favicon);
    void zoomFactorChanged(double factor);
    void downloadRequested(QWebEngineDownloadRequest *download);

private slots:
    void onUrlChanged(const QUrl &url);
    void onTitleChanged(const QString &title);
    void onLoadStarted();
    void onLoadFinished(bool success);
    void onFaviconLoaded(const QUrl &url, const QPixmap &favicon);

private:
    QVBoxLayout *layout;
    QWebEngineView *m_webView;
    PrivacyEngine *privacyEngine;
    DevTools *devTools;
    FaviconManager *faviconManager;
    QPixmap currentFavicon;
    double m_zoomFactor;
    bool m_readerMode;
    bool m_muted;
    
    void setupFindInPage();
};

#endif // BROWSERWINDOW_H
