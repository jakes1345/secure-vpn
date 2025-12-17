#include "downloadmanager.h"
#include <QStandardPaths>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QDateTime>
#include <QNetworkAccessManager>
#include <QNetworkRequest>
#include <QNetworkReply>

DownloadItem::DownloadItem(QWebEngineDownloadRequest *download, QObject *parent)
    : QObject(parent)
    , m_download(download)
    , m_url(download->url())
    , m_filename(download->downloadFileName())
    , m_path(download->downloadDirectory() + "/" + m_filename)
    , m_bytesReceived(0)
    , m_bytesTotal(0)
    , m_finished(false)
    , m_paused(false)
{
    connect(download, &QWebEngineDownloadRequest::receivedBytesChanged, this, [this]() {
        if (m_download) {
            onDownloadProgress(m_download->receivedBytes(), m_download->totalBytes());
        }
    });
    connect(download, &QWebEngineDownloadRequest::totalBytesChanged, this, [this]() {
        if (m_download) {
            onDownloadProgress(m_download->receivedBytes(), m_download->totalBytes());
        }
    });
    connect(download, &QWebEngineDownloadRequest::isFinishedChanged, this, [this]() {
        if (m_download && m_download->isFinished()) {
            onFinished();
        }
    });
    
    m_bytesTotal = download->totalBytes();
    m_bytesReceived = download->receivedBytes();
}

DownloadItem::DownloadItem(const QUrl &url, const QString &filename, QObject *parent)
    : QObject(parent)
    , m_download(nullptr)
    , m_url(url)
    , m_filename(filename.isEmpty() ? url.fileName() : filename)
    , m_bytesReceived(0)
    , m_bytesTotal(0)
    , m_finished(false)
    , m_paused(false)
{
    // Manual download via QNetworkAccessManager
    // This will be handled separately
}

QString DownloadItem::filename() const
{
    return m_filename;
}

QString DownloadItem::path() const
{
    return m_path;
}

qint64 DownloadItem::bytesReceived() const
{
    return m_bytesReceived;
}

qint64 DownloadItem::bytesTotal() const
{
    return m_bytesTotal;
}

double DownloadItem::progress() const
{
    if (m_bytesTotal == 0) return 0.0;
    return static_cast<double>(m_bytesReceived) / static_cast<double>(m_bytesTotal);
}

bool DownloadItem::isFinished() const
{
    return m_finished;
}

bool DownloadItem::isPaused() const
{
    return m_paused;
}

QUrl DownloadItem::url() const
{
    return m_url;
}

void DownloadItem::pause()
{
    if (m_download && !m_finished) {
        m_download->pause();
        m_paused = true;
    }
}

void DownloadItem::resume()
{
    if (m_download && m_paused) {
        m_download->resume();
        m_paused = false;
    }
}

void DownloadItem::cancel()
{
    if (m_download) {
        m_download->cancel();
        m_finished = true;
    }
}

void DownloadItem::onDownloadProgress(qint64 bytesReceived, qint64 bytesTotal)
{
    m_bytesReceived = bytesReceived;
    m_bytesTotal = bytesTotal;
    emit progressChanged();
}

void DownloadItem::onFinished()
{
    m_finished = true;
    m_paused = false;
    if (m_download) {
        m_bytesReceived = m_download->receivedBytes();
        m_bytesTotal = m_download->totalBytes();
    }
    emit finished();
}

void DownloadItem::onFailed()
{
    m_finished = true;
    emit failed("Download failed");
}

DownloadManager::DownloadManager(QObject *parent)
    : QObject(parent)
{
    m_defaultPath = QStandardPaths::writableLocation(QStandardPaths::DownloadLocation);
    loadHistory();
}

QList<DownloadItem*> DownloadManager::downloads() const
{
    return m_downloads;
}

DownloadItem* DownloadManager::downloadAt(int index) const
{
    if (index >= 0 && index < m_downloads.size()) {
        return m_downloads.at(index);
    }
    return nullptr;
}

int DownloadManager::downloadCount() const
{
    return m_downloads.size();
}

void DownloadManager::addDownload(QWebEngineDownloadRequest *download)
{
    DownloadItem *item = new DownloadItem(download, this);
    m_downloads.append(item);
    
    connect(item, &DownloadItem::finished, this, &DownloadManager::onDownloadFinished);
    connect(item, &DownloadItem::failed, this, &DownloadManager::onDownloadFailed);
    
    emit downloadAdded(item);
}

void DownloadManager::addDownload(const QUrl &url, const QString &filename)
{
    // Create manual download item
    DownloadItem *item = new DownloadItem(url, filename, this);
    m_downloads.append(item);
    
    // TODO: Implement manual download via QNetworkAccessManager
    
    emit downloadAdded(item);
}

QString DownloadManager::defaultDownloadPath() const
{
    return m_defaultPath;
}

void DownloadManager::setDefaultDownloadPath(const QString &path)
{
    m_defaultPath = path;
}

QJsonArray DownloadManager::getDownloadHistory() const
{
    return m_history;
}

void DownloadManager::clearHistory()
{
    m_history = QJsonArray();
    saveHistory();
}

void DownloadManager::onDownloadFinished()
{
    DownloadItem *item = qobject_cast<DownloadItem*>(sender());
    if (item) {
        // Add to history
        QJsonObject entry;
        entry["url"] = item->url().toString();
        entry["filename"] = item->filename();
        entry["path"] = item->path();
        entry["finished"] = QDateTime::currentDateTime().toString(Qt::ISODate);
        entry["size"] = static_cast<qint64>(item->bytesTotal());
        
        m_history.prepend(entry);
        
        // Keep only last 100
        if (m_history.size() > 100) {
            QJsonArray newHistory;
            for (int i = 0; i < 100; i++) {
                newHistory.append(m_history.at(i));
            }
            m_history = newHistory;
        }
        
        saveHistory();
        emit downloadFinished(item);
    }
}

void DownloadManager::onDownloadFailed()
{
    DownloadItem *item = qobject_cast<DownloadItem*>(sender());
    if (item) {
        emit downloadFailed(item, "Download failed");
    }
}

void DownloadManager::loadHistory()
{
    QFile file(getHistoryPath());
    if (file.open(QIODevice::ReadOnly)) {
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        m_history = doc.array();
    }
}

void DownloadManager::saveHistory()
{
    QDir dir;
    dir.mkpath(QFileInfo(getHistoryPath()).absolutePath());
    
    QFile file(getHistoryPath());
    if (file.open(QIODevice::WriteOnly)) {
        QJsonDocument doc(m_history);
        file.write(doc.toJson());
    }
}

QString DownloadManager::getHistoryPath() const
{
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::ConfigLocation);
    return configDir + "/phazebrowser/downloads.json";
}
