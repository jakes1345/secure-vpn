#include "searchmanager.h"
#include <QStandardPaths>
#include <QDir>
#include <QFile>
#include <QFileInfo>
#include <QJsonDocument>
#include <QJsonArray>
#include <QJsonObject>
#include <QUrlQuery>

SearchManager::SearchManager(QObject *parent)
    : QObject(parent)
{
    // Default search engines
    m_engines.append(SearchEngine("Google", "google", "https://www.google.com/search?q=%s", true));
    m_engines.append(SearchEngine("DuckDuckGo", "ddg", "https://duckduckgo.com/?q=%s"));
    m_engines.append(SearchEngine("Bing", "bing", "https://www.bing.com/search?q=%s"));
    m_engines.append(SearchEngine("Yahoo", "yahoo", "https://search.yahoo.com/search?p=%s"));
    m_engines.append(SearchEngine("Startpage", "startpage", "https://www.startpage.com/sp/search?query=%s"));
    
    m_defaultKeyword = "google";
    
    loadEngines();
}

QList<SearchEngine> SearchManager::searchEngines() const
{
    return m_engines;
}

SearchEngine SearchManager::defaultEngine() const
{
    for (const SearchEngine &engine : m_engines) {
        if (engine.keyword == m_defaultKeyword) {
            return engine;
        }
    }
    return m_engines.isEmpty() ? SearchEngine() : m_engines.first();
}

void SearchManager::setDefaultEngine(const QString &keyword)
{
    m_defaultKeyword = keyword;
    saveEngines();
}

void SearchManager::addEngine(const SearchEngine &engine)
{
    m_engines.append(engine);
    saveEngines();
}

void SearchManager::removeEngine(const QString &keyword)
{
    for (int i = 0; i < m_engines.size(); i++) {
        if (m_engines.at(i).keyword == keyword) {
            m_engines.removeAt(i);
            break;
        }
    }
    saveEngines();
}

void SearchManager::updateEngine(const QString &keyword, const SearchEngine &engine)
{
    for (int i = 0; i < m_engines.size(); i++) {
        if (m_engines.at(i).keyword == keyword) {
            m_engines[i] = engine;
            break;
        }
    }
    saveEngines();
}

QUrl SearchManager::searchUrl(const QString &query, const QString &engineKeyword) const
{
    QString keyword = engineKeyword.isEmpty() ? m_defaultKeyword : engineKeyword;
    
    for (const SearchEngine &engine : m_engines) {
        if (engine.keyword == keyword) {
            return engine.searchUrl(query);
        }
    }
    
    // Fallback to default
    return defaultEngine().searchUrl(query);
}

QStringList SearchManager::suggestions(const QString &query) const
{
    // TODO: Implement search suggestions
    Q_UNUSED(query);
    return QStringList();
}

void SearchManager::loadEngines()
{
    QFile file(getEnginesPath());
    if (file.open(QIODevice::ReadOnly)) {
        QJsonDocument doc = QJsonDocument::fromJson(file.readAll());
        QJsonObject obj = doc.object();
        
        m_defaultKeyword = obj["default"].toString();
        
        QJsonArray engines = obj["engines"].toArray();
        m_engines.clear();
        for (const QJsonValue &value : engines) {
            QJsonObject eng = value.toObject();
            SearchEngine engine;
            engine.name = eng["name"].toString();
            engine.keyword = eng["keyword"].toString();
            engine.url = eng["url"].toString();
            engine.isDefault = eng["default"].toBool();
            m_engines.append(engine);
        }
    }
}

void SearchManager::saveEngines()
{
    QDir dir;
    dir.mkpath(QFileInfo(getEnginesPath()).absolutePath());
    
    QJsonObject obj;
    obj["default"] = m_defaultKeyword;
    
    QJsonArray engines;
    for (const SearchEngine &engine : m_engines) {
        QJsonObject eng;
        eng["name"] = engine.name;
        eng["keyword"] = engine.keyword;
        eng["url"] = engine.url;
        eng["default"] = engine.isDefault;
        engines.append(eng);
    }
    obj["engines"] = engines;
    
    QFile file(getEnginesPath());
    if (file.open(QIODevice::WriteOnly)) {
        QJsonDocument doc(obj);
        file.write(doc.toJson());
    }
}

QString SearchManager::getEnginesPath() const
{
    QString configDir = QStandardPaths::writableLocation(QStandardPaths::ConfigLocation);
    return configDir + "/phazebrowser/search_engines.json";
}

QUrl SearchEngine::searchUrl(const QString &query) const
{
    QString searchUrl = url;
    QString encodedQuery = QUrl::toPercentEncoding(query);
    searchUrl.replace("%s", encodedQuery);
    return QUrl(searchUrl);
}
