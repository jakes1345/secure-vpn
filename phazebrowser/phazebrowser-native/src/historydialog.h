#ifndef HISTORYDIALOG_H
#define HISTORYDIALOG_H

#include <QDialog>
#include <QVBoxLayout>
#include <QHBoxLayout>
#include <QTableWidget>
#include <QPushButton>
#include <QLineEdit>
#include <QDateEdit>
#include <QComboBox>
#include "datamanager.h"

class HistoryDialog : public QDialog
{
    Q_OBJECT

public:
    explicit HistoryDialog(DataManager *dataManager, QWidget *parent = nullptr);

private slots:
    void onSearchHistory(const QString &text);
    void onFilterByDate();
    void onDeleteSelected();
    void onClearAll();
    void onItemDoubleClicked(int row, int column);

signals:
    void urlSelected(const QUrl &url);

private:
    void setupUI();
    void loadHistory();
    void updateTable();
    
    DataManager *dataManager;
    QTableWidget *historyTable;
    QLineEdit *searchBox;
    QDateEdit *dateFilter;
    QComboBox *filterCombo;
    QPushButton *deleteBtn;
    QPushButton *clearAllBtn;
};

#endif // HISTORYDIALOG_H
