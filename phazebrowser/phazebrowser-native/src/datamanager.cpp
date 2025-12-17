#include "datamanager.h"
#include <QStandardPaths>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonObject>
#include <QJsonArray>
#include <QCryptographicHash>
#include <QDataStream>
#include <QByteArray>

DataManager::DataManager(QObject *parent)
    : QObject(parent)
{
    loadBookmarks();
    loadHistory();
    loadPasswords();
    loadSettings();
    loadSession();
}

QString DataManager::getBookmarksPath() const
{
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::ConfigLocation);
    return configDir + "/phazebrowser/bookmarks.json";
}

QString DataManager::getHistoryPath() const
{
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::ConfigLocation);
    return configDir + "/phazebrowser/history.json";
}

QString DataManager::getPasswordsPath() const
{
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::ConfigLocation);
    return configDir + "/phazebrowser/passwords.json";
}

QString DataManager::getSettingsPath() const
{
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::ConfigLocation);
    return configDir + "/phazebrowser/settings.json";
}

QString DataManager::getSessionPath() const
{
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::ConfigLocation);
    return configDir + "/phazebrowser/session.json";
}

void DataManager::loadBookmarks()
{
    QFile file(getBookmarksPath());
    if (file.open(QIODevice::ReadOnly)) {
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        m_bookmarks = doc.array();
    }
}

void DataManager::loadHistory()
{
    QFile file(getHistoryPath());
    if (file.open(QIODevice::ReadOnly)) {
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        m_history = doc.array();
        
        // Keep only last 1000 entries
        if (m_history.size() > 1000) {
            QJsonArray newHistory;
            for (int i = 0; i < 1000; i++) {
                newHistory.append(m_history.at(i));
            }
            m_history = newHistory;
        }
    }
}

void DataManager::loadPasswords()
{
    QFile file(getPasswordsPath());
    if (file.open(QIODevice::ReadOnly)) {
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        m_passwords = doc.array();
    }
}

void DataManager::loadSettings()
{
    QFile file(getSettingsPath());
    if (file.open(QIODevice::ReadOnly)) {
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        m_settings = doc.object();
    } else {
        // Default settings
        m_settings["adBlocking"] = true;
        m_settings["trackingProtection"] = true;
        m_settings["fingerprintProtection"] = true;
        m_settings["cookieBlocking"] = true;
        m_settings["blockAllCookies"] = true;
        m_settings["blockFonts"] = true;
        m_settings["blockCamera"] = true;
        m_settings["blockMicrophone"] = true;
        m_settings["blockGeolocation"] = true;
        m_settings["blockNotifications"] = true;
        m_settings["theme"] = "dark";
    }
}

QJsonArray DataManager::getBookmarks() const
{
    return m_bookmarks;
}

void DataManager::addBookmark(const QString &url, const QString &title)
{
    QJsonObject bookmark;
    bookmark["url"] = url;
    bookmark["title"] = title;
    bookmark["added"] = QDateTime::currentDateTime().toString(Qt::ISODate);
    
    // Remove if exists
    QJsonArray newBookmarks;
    for (const QJsonValue &value : m_bookmarks) {
        QJsonObject obj = value.toObject();
        if (obj["url"].toString() != url) {
            newBookmarks.append(value);
        }
    }
    
    // Add to front
    newBookmarks.prepend(bookmark);
    m_bookmarks = newBookmarks;
    saveBookmarks();
}

void DataManager::removeBookmark(const QString &url)
{
    QJsonArray newBookmarks;
    for (const QJsonValue &value : m_bookmarks) {
        QJsonObject obj = value.toObject();
        if (obj["url"].toString() != url) {
            newBookmarks.append(value);
        }
    }
    m_bookmarks = newBookmarks;
    saveBookmarks();
}

void DataManager::saveBookmarks()
{
    QDir dir;
    dir.mkpath(QFileInfo(getBookmarksPath()).absolutePath());
    
    QFile file(getBookmarksPath());
    if (file.open(QIODevice::WriteOnly)) {
        QJsonDocument doc(m_bookmarks);
        file.write(doc.toJson());
    }
}

QJsonArray DataManager::getHistory() const
{
    return m_history;
}

void DataManager::addHistory(const QString &url, const QString &title)
{
    QJsonObject entry;
    entry["url"] = url;
    entry["title"] = title;
    entry["timestamp"] = QDateTime::currentDateTime().toString(Qt::ISODate);
    
    // Remove if exists
    QJsonArray newHistory;
    for (const QJsonValue &value : m_history) {
        QJsonObject obj = value.toObject();
        if (obj["url"].toString() != url) {
            newHistory.append(value);
        }
    }
    
    // Add to front
    newHistory.prepend(entry);
    
    // Keep only last 1000
    if (newHistory.size() > 1000) {
        QJsonArray trimmed;
        for (int i = 0; i < 1000; i++) {
            trimmed.append(newHistory.at(i));
        }
        newHistory = trimmed;
    }
    
    m_history = newHistory;
    saveHistory();
}

void DataManager::clearHistory()
{
    m_history = QJsonArray();
    saveHistory();
}

void DataManager::saveHistory()
{
    QDir dir;
    dir.mkpath(QFileInfo(getHistoryPath()).absolutePath());
    
    QFile file(getHistoryPath());
    if (file.open(QIODevice::WriteOnly)) {
        QJsonDocument doc(m_history);
        file.write(doc.toJson());
    }
}

QJsonArray DataManager::getPasswords() const
{
    return m_passwords;
}

void DataManager::addPassword(const QString &url, const QString &username, const QString &password)
{
    QJsonObject entry;
    entry["url"] = url;
    entry["username"] = username;
    entry["password"] = encryptPassword(password);
    entry["added"] = QDateTime::currentDateTime().toString(Qt::ISODate);
    
    // Remove if exists
    QJsonArray newPasswords;
    for (const QJsonValue &value : m_passwords) {
        QJsonObject obj = value.toObject();
        if (obj["url"].toString() != url || obj["username"].toString() != username) {
            newPasswords.append(value);
        }
    }
    
    newPasswords.append(entry);
    m_passwords = newPasswords;
    savePasswords();
}

void DataManager::removePassword(const QString &url)
{
    QJsonArray newPasswords;
    for (const QJsonValue &value : m_passwords) {
        QJsonObject obj = value.toObject();
        if (obj["url"].toString() != url) {
            newPasswords.append(value);
        }
    }
    m_passwords = newPasswords;
    savePasswords();
}

void DataManager::savePasswords()
{
    QDir dir;
    dir.mkpath(QFileInfo(getPasswordsPath()).absolutePath());
    
    QFile file(getPasswordsPath());
    if (file.open(QIODevice::WriteOnly)) {
        QJsonDocument doc(m_passwords);
        file.write(doc.toJson());
    }
}

QJsonObject DataManager::getSettings() const
{
    return m_settings;
}

void DataManager::setSettings(const QJsonObject &settings)
{
    m_settings = settings;
    saveSettings();
}

void DataManager::saveSettings()
{
    QDir dir;
    dir.mkpath(QFileInfo(getSettingsPath()).absolutePath());
    
    QFile file(getSettingsPath());
    if (file.open(QIODevice::WriteOnly)) {
        QJsonDocument doc(m_settings);
        file.write(doc.toJson());
    }
}

void DataManager::loadSession()
{
    QFile file(getSessionPath());
    if (file.open(QIODevice::ReadOnly)) {
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        m_session = doc.array();
    }
}

QJsonArray DataManager::getSession() const
{
    return m_session;
}

void DataManager::setSession(const QJsonArray &session)
{
    m_session = session;
    saveSession();
}

void DataManager::saveSession()
{
    QDir dir;
    dir.mkpath(QFileInfo(getSessionPath()).absolutePath());
    
    QFile file(getSessionPath());
    if (file.open(QIODevice::WriteOnly)) {
        QJsonDocument doc(m_session);
        file.write(doc.toJson());
    }
}

void DataManager::clearSession()
{
    m_session = QJsonArray();
    saveSession();
}

QString DataManager::encryptPassword(const QString &password) const
{
    // Simple XOR encryption (for now - can be improved)
    QString key = "PhazeBrowser2025";
    QString encrypted;
    for (int i = 0; i < password.length(); i++) {
        encrypted.append(QChar(password[i].unicode() ^ key[i % key.length()].unicode()));
    }
    return encrypted.toUtf8().toBase64();
}

QString DataManager::decryptPassword(const QString &encrypted) const
{
    return decryptPasswordStatic(encrypted);
}

QString DataManager::decryptPasswordStatic(const QString &encrypted)
{
    QString decoded = QByteArray::fromBase64(encrypted.toUtf8());
    QString key = "PhazeBrowser2025";
    QString decrypted;
    for (int i = 0; i < decoded.length(); i++) {
        decrypted.append(QChar(decoded[i].unicode() ^ key[i % key.length()].unicode()));
    }
    return decrypted;
}
