#include "faviconmanager.h"
#include <QNetworkRequest>
#include <QPixmap>
#include <QIcon>
#include <QFileInfo>

FaviconManager::FaviconManager(QObject *parent)
    : QObject(parent)
    , m_networkManager(new QNetworkAccessManager(this))
    , m_cache(100) // Cache 100 favicons
{
    connect(m_networkManager, &QNetworkAccessManager::finished, this, &FaviconManager::onFaviconLoaded);
}

QPixmap FaviconManager::favicon(const QUrl &url) const
{
    QString key = cacheKey(url);
    QPixmap *cached = m_cache.object(key);
    if (cached) {
        return *cached;
    }
    
    // Return default icon
    return QPixmap(":/icons/default-favicon.png");
}

void FaviconManager::loadFavicon(const QUrl &url)
{
    QString key = cacheKey(url);
    if (m_cache.contains(key)) {
        QPixmap *cached = m_cache.object(key);
        emit faviconLoaded(url, *cached);
        return;
    }
    
    QUrl faviconUrl = this->faviconUrl(url);
    QNetworkRequest request(faviconUrl);
    request.setAttribute(QNetworkRequest::User, url);
    m_networkManager->get(request);
}

void FaviconManager::onFaviconLoaded(QNetworkReply *reply)
{
    QUrl pageUrl = reply->request().attribute(QNetworkRequest::User).toUrl();
    
    if (reply->error() == QNetworkReply::NoError) {
        QPixmap pixmap;
        if (pixmap.loadFromData(reply->readAll())) {
            QString key = cacheKey(pageUrl);
            m_cache.insert(key, new QPixmap(pixmap));
            emit faviconLoaded(pageUrl, pixmap);
        }
    }
    
    reply->deleteLater();
}

QString FaviconManager::cacheKey(const QUrl &url) const
{
    return url.host();
}

QUrl FaviconManager::faviconUrl(const QUrl &pageUrl) const
{
    // Try common favicon locations
    QString host = pageUrl.scheme() + "://" + pageUrl.host();
    
    // Try /favicon.ico first
    QUrl faviconUrl = QUrl(host + "/favicon.ico");
    return faviconUrl;
}
