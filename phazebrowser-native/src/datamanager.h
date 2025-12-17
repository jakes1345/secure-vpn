#ifndef DATAMANAGER_H
#define DATAMANAGER_H

#include <QObject>
#include <QJsonArray>
#include <QJsonObject>
#include <QString>
#include <QDateTime>

class DataManager : public QObject
{
    Q_OBJECT

public:
    explicit DataManager(QObject *parent = nullptr);
    
    // Bookmarks
    QJsonArray getBookmarks() const;
    void addBookmark(const QString &url, const QString &title);
    void removeBookmark(const QString &url);
    void saveBookmarks();
    
    // History
    QJsonArray getHistory() const;
    void addHistory(const QString &url, const QString &title);
    void clearHistory();
    void saveHistory();
    
    // Passwords (encrypted)
    QJsonArray getPasswords() const;
    void addPassword(const QString &url, const QString &username, const QString &password);
    void removePassword(const QString &url);
    void savePasswords();
    
    // Settings
    QJsonObject getSettings() const;
    void setSettings(const QJsonObject &settings);
    void saveSettings();
    
    // Session (tabs)
    QJsonArray getSession() const;
    void setSession(const QJsonArray &session);
    void saveSession();
    void clearSession();

private:
    QString getBookmarksPath() const;
    QString getHistoryPath() const;
    QString getPasswordsPath() const;
    QString getSettingsPath() const;
    QString getSessionPath() const;
    
    QJsonArray m_bookmarks;
    QJsonArray m_history;
    QJsonArray m_passwords;
    QJsonObject m_settings;
    QJsonArray m_session;
    
    void loadBookmarks();
    void loadHistory();
    void loadPasswords();
    void loadSettings();
    void loadSession();
    
    QString encryptPassword(const QString &password) const;
    QString decryptPassword(const QString &encrypted) const;
    
public:
    // Public decrypt for password dialog
    static QString decryptPasswordStatic(const QString &encrypted);
};

#endif // DATAMANAGER_H
