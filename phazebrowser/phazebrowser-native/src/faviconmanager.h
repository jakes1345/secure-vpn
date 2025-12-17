#ifndef FAVICONMANAGER_H
#define FAVICONMANAGER_H

#include <QObject>
#include <QUrl>
#include <QPixmap>
#include <QCache>
#include <QNetworkAccessManager>
#include <QNetworkReply>

class FaviconManager : public QObject
{
    Q_OBJECT

public:
    explicit FaviconManager(QObject *parent = nullptr);
    
    QPixmap favicon(const QUrl &url) const;
    void loadFavicon(const QUrl &url);

signals:
    void faviconLoaded(const QUrl &url, const QPixmap &pixmap);

private slots:
    void onFaviconLoaded(QNetworkReply *reply);

private:
    QNetworkAccessManager *m_networkManager;
    mutable QCache<QString, QPixmap> m_cache;
    
    QString cacheKey(const QUrl &url) const;
    QUrl faviconUrl(const QUrl &pageUrl) const;
};

#endif // FAVICONMANAGER_H
