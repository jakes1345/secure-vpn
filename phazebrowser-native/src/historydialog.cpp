#include "historydialog.h"
#include "datamanager.h"
#include <QHeaderView>
#include <QMessageBox>
#include <QDateTime>
#include <QUrl>
#include <QSet>
#include <QLabel>
#include <QLineEdit>
#include <QComboBox>
#include <QPushButton>
#include <QTableWidget>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <algorithm>

HistoryDialog::HistoryDialog(DataManager *dataManager, QWidget *parent)
    : QDialog(parent)
    , dataManager(dataManager)
{
    setWindowTitle("History");
    setMinimumSize(800, 600);
    setupUI();
    loadHistory();
}

void HistoryDialog::setupUI()
{
    QVBoxLayout *mainLayout = new QVBoxLayout(this);
    
    // Filters
    QHBoxLayout *filterLayout = new QHBoxLayout();
    
    searchBox = new QLineEdit(this);
    searchBox->setPlaceholderText("Search history...");
    searchBox->setStyleSheet("padding: 6px 12px; background: #3d3d3d; border: 1px solid #404040; border-radius: 4px;");
    connect(searchBox, &QLineEdit::textChanged, this, &HistoryDialog::onSearchHistory);
    filterLayout->addWidget(searchBox);
    
    dateFilter = new QDateEdit(this);
    dateFilter->setDate(QDate::currentDate());
    dateFilter->setCalendarPopup(true);
    connect(dateFilter, &QDateEdit::dateChanged, this, &HistoryDialog::onFilterByDate);
    filterLayout->addWidget(new QLabel("Date:"));
    filterLayout->addWidget(dateFilter);
    
    filterCombo = new QComboBox(this);
    filterCombo->addItems(QStringList() << "All" << "Today" << "This Week" << "This Month");
    connect(filterCombo, QOverload<int>::of(&QComboBox::currentIndexChanged), this, &HistoryDialog::onFilterByDate);
    filterLayout->addWidget(filterCombo);
    
    mainLayout->addLayout(filterLayout);
    
    // History table
    historyTable = new QTableWidget(this);
    historyTable->setColumnCount(3);
    historyTable->setHorizontalHeaderLabels(QStringList() << "Title" << "URL" << "Date");
    historyTable->horizontalHeader()->setStretchLastSection(true);
    historyTable->setSelectionBehavior(QAbstractItemView::SelectRows);
    historyTable->setSelectionMode(QAbstractItemView::ExtendedSelection);
    historyTable->setEditTriggers(QAbstractItemView::NoEditTriggers);
    historyTable->setStyleSheet(
        "QTableWidget { background: #1e1e1e; color: white; gridline-color: #404040; }"
        "QTableWidget::item { padding: 8px; }"
        "QHeaderView::section { background: #2d2d2d; color: white; padding: 8px; }"
    );
    connect(historyTable, &QTableWidget::cellDoubleClicked, this, &HistoryDialog::onItemDoubleClicked);
    
    mainLayout->addWidget(historyTable);
    
    // Buttons
    QHBoxLayout *buttonLayout = new QHBoxLayout();
    
    deleteBtn = new QPushButton("🗑️ Delete Selected");
    deleteBtn->setEnabled(false);
    connect(deleteBtn, &QPushButton::clicked, this, &HistoryDialog::onDeleteSelected);
    buttonLayout->addWidget(deleteBtn);
    
    clearAllBtn = new QPushButton("🗑️ Clear All");
    connect(clearAllBtn, &QPushButton::clicked, this, &HistoryDialog::onClearAll);
    buttonLayout->addWidget(clearAllBtn);
    
    buttonLayout->addStretch();
    
    QPushButton *closeBtn = new QPushButton("Close");
    connect(closeBtn, &QPushButton::clicked, this, &QDialog::accept);
    buttonLayout->addWidget(closeBtn);
    
    mainLayout->addLayout(buttonLayout);
    
    // Connect selection
    connect(historyTable, &QTableWidget::itemSelectionChanged, [this]() {
        bool hasSelection = historyTable->selectedItems().size() > 0;
        deleteBtn->setEnabled(hasSelection);
    });
}

void HistoryDialog::loadHistory()
{
    updateTable();
}

void HistoryDialog::updateTable()
{
    historyTable->setRowCount(0);
    
    QJsonArray history = dataManager->getHistory();
    for (const QJsonValue &value : history) {
        QJsonObject entry = value.toObject();
        int row = historyTable->rowCount();
        historyTable->insertRow(row);
        
        historyTable->setItem(row, 0, new QTableWidgetItem(entry["title"].toString()));
        historyTable->setItem(row, 1, new QTableWidgetItem(entry["url"].toString()));
        
        QDateTime timestamp = QDateTime::fromString(entry["timestamp"].toString(), Qt::ISODate);
        historyTable->setItem(row, 2, new QTableWidgetItem(timestamp.toString("yyyy-MM-dd hh:mm:ss")));
        historyTable->item(row, 2)->setData(Qt::UserRole, entry["url"].toString());
    }
}

void HistoryDialog::onSearchHistory(const QString &text)
{
    // Filter table by search text
    for (int i = 0; i < historyTable->rowCount(); i++) {
        bool match = false;
        if (text.isEmpty()) {
            match = true;
        } else {
            QString title = historyTable->item(i, 0)->text().toLower();
            QString url = historyTable->item(i, 1)->text().toLower();
            match = title.contains(text.toLower()) || url.contains(text.toLower());
        }
        historyTable->setRowHidden(i, !match);
    }
}

void HistoryDialog::onFilterByDate()
{
    QDate filterDate = dateFilter->date();
    int filterType = filterCombo->currentIndex();
    
    for (int i = 0; i < historyTable->rowCount(); i++) {
        QDateTime timestamp = QDateTime::fromString(historyTable->item(i, 2)->text(), "yyyy-MM-dd hh:mm:ss");
        QDate entryDate = timestamp.date();
        
        bool match = false;
        switch (filterType) {
            case 0: // All
                match = true;
                break;
            case 1: // Today
                match = entryDate == QDate::currentDate();
                break;
            case 2: // This Week
                match = entryDate >= QDate::currentDate().addDays(-7);
                break;
            case 3: // This Month
                match = entryDate.month() == QDate::currentDate().month();
                break;
        }
        
        historyTable->setRowHidden(i, !match);
    }
}

void HistoryDialog::onDeleteSelected()
{
    QList<QTableWidgetItem*> selected = historyTable->selectedItems();
    if (selected.isEmpty()) return;
    
    int ret = QMessageBox::question(this, "Delete History", "Are you sure you want to delete selected history entries?");
    if (ret == QMessageBox::Yes) {
        QSet<int> rowsToDelete;
        for (QTableWidgetItem *item : selected) {
            rowsToDelete.insert(item->row());
        }
        
        // TODO: Delete from data manager
        // For now, just remove from table
        QList<int> sortedRows = rowsToDelete.values();
        std::sort(sortedRows.begin(), sortedRows.end(), std::greater<int>());
        for (int row : sortedRows) {
            historyTable->removeRow(row);
        }
    }
}

void HistoryDialog::onClearAll()
{
    int ret = QMessageBox::question(this, "Clear All History", "Are you sure you want to clear all history?");
    if (ret == QMessageBox::Yes) {
        dataManager->clearHistory();
        updateTable();
    }
}

void HistoryDialog::onItemDoubleClicked(int row, int column)
{
    Q_UNUSED(column);
    if (row >= 0 && row < historyTable->rowCount()) {
        QString url = historyTable->item(row, 1)->text();
        if (!url.isEmpty()) {
            emit urlSelected(QUrl(url));
            accept();
        }
    }
}
