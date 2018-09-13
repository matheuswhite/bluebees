import QtQuick 2.5
import QtQuick.Controls 1.4
import QtQuick.Layouts 1.2

ApplicationWindow {
    visible: true
    width: 640
    height: 240
    title: qsTr("Test Qt with Async")
    color: "whitesmoke"

    GridLayout {

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.margins: 9

        columns: 4
        rows: 4
        rowSpacing: 10
        columnSpacing: 10

        Button {
            height: 40
            Layout.fillWidth: true
            text: qsTr("Read data")
            id: readBtn

            Layout.columnSpan: 2

            onClicked: {
                // Invoke the calculator slot to sum the numbers
                consumer1.start_read()
            }
        }

        Text {
            text: qsTr("Data Read")
        }

        // Here we see the result of sum
        Text {
            id: dataRead
        }
    }

    // Here we take the result of sum or subtracting numbers
    Connections {
        target: consumer1

        // Sum signal handler
        onDataRead: {
            // sum was set through arguments=['sum']
            dataRead.text = data
        }

        onReadingStarted: {
            readBtn.enabled = false
        }

        onReadingCompleted: {
            readBtn.enabled = true
        }
    }
}