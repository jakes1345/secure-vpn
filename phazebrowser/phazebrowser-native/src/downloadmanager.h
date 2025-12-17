#ifndef DOWNLOADMANAGER_H
#define DOWNLOADMANAGER_H

#include <QObject>
#include <QWebEngineDownloadRequest>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QFile>
#include <QTimer>
#include <QJsonArray>
#include <QJsonObject>
#include <QUrl>

class DownloadItem : public QObject
{
    Q_OBJECT

public:
    DownloadItem(QWebEngineDownloadRequest *download, QObject *parent = nullptr);
    DownloadItem(const QUrl &url, const QString &filename, QObject *parent = nullptr);
    
    QString filename() const;
    QString path() const;
    qint64 bytesReceived() const;
    qint64 bytesTotal() const;
    double progress() const;
    bool isFinished() const;
    bool isPaused() const;
    QUrl url() const;
    
    void pause();
    void resume();
    void cancel();

signals:
    void progressChanged();
    void finished();
    void failed(const QString &error);

private slots:
    void onDownloadProgress(qint64 bytesReceived, qint64 bytesTotal);
    void onFinished();
    void onFailed();

private:
    QWebEngineDownloadRequest *m_download;
    QUrl m_url;
    QString m_filename;
    QString m_path;
    qint64 m_bytesReceived;
    qint64 m_bytesTotal;
    bool m_finished;
    bool m_paused;
};

class DownloadManager : public QObject
{
    Q_OBJECT

public:
    explicit DownloadManager(QObject *parent = nullptr);
    
    QList<DownloadItem*> downloads() const;
    DownloadItem* downloadAt(int index) const;
    int downloadCount() const;
    
    void addDownload(QWebEngineDownloadRequest *download);
    void addDownload(const QUrl &url, const QString &filename = QString());
    
    QString defaultDownloadPath() const;
    void setDefaultDownloadPath(const QString &path);
    
    QJsonArray getDownloadHistory() const;
    void clearHistory();

signals:
    void downloadAdded(DownloadItem *item);
    void downloadFinished(DownloadItem *item);
    void downloadFailed(DownloadItem *item, const QString &error);

private slots:
    void onDownloadFinished();
    void onDownloadFailed();

private:
    QList<DownloadItem*> m_downloads;
    QString m_defaultPath;
    QJsonArray m_history;
    
    void loadHistory();
    void saveHistory();
    QString getHistoryPath() const;
};

#endif // DOWNLOADMANAGER_H
