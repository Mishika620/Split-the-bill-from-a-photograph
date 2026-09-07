// =====================================================
// DOM ELEMENTS
// =====================================================

const itemsBody = document.getElementById("itemsBody");

const subtotalElement =
    document.getElementById("subtotal");

const totalElement =
    document.getElementById("total");

const itemCount =
    document.getElementById("itemCount");

const validationCard =
    document.getElementById("validationCard");

const validationTitle =
    document.getElementById("validationTitle");

const validationMessage =
    document.getElementById("validationMessage");

const toast =
    document.getElementById("toast");

const overallConfidence =
    document.getElementById("overallConfidence");


// =====================================================
// BILL STATE
// =====================================================

let bill = {

    items: [
        {
            name: "Margherita Pizza",
            quantity: 2,
            unit_price: 225,
            total_price: 450,

            name_confidence: 0.95,
            quantity_confidence: 0.96,
            price_confidence: 0.95,
            confidence: 0.95,

            assigned_to: []
        },

        {
            name: "Garlic Bread",
            quantity: 1,
            unit_price: 180,
            total_price: 180,

            name_confidence: 0.91,
            quantity_confidence: 0.95,
            price_confidence: 0.92,
            confidence: 0.91,

            assigned_to: []
        },

        {
            name: "Coke",
            quantity: 2,
            unit_price: 60,
            total_price: 120,

            name_confidence: 0.96,
            quantity_confidence: 0.95,
            price_confidence: 0.96,
            confidence: 0.96,

            assigned_to: []
        }
    ],

    subtotal: 750,
    tax: 75,
    service_charge: 30,
    discount: 0,
    total: 855,

    subtotal_confidence: 0.95,
    tax_confidence: 0.95,
    service_charge_confidence: 0.95,
    discount_confidence: 0.95,
    total_confidence: 0.95,

    confidence: 0.94
};


// =====================================================
// PEOPLE STATE
// =====================================================

let people = [

    {
        id: "person-you",
        name: "You"
    },

    {
        id: "person-alex",
        name: "Alex"
    }

];


// =====================================================
// HELPERS
// =====================================================

function formatMoney(value) {

    return `₹${Number(value || 0).toFixed(2)}`;

}


function showToast(message) {

    if (!toast) {
        return;
    }

    toast.textContent = message;

    toast.classList.add("show");

    setTimeout(() => {

        toast.classList.remove("show");

    }, 1800);

}


function escapeHtml(value) {

    return String(value)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


function getInitial(name) {

    return String(name)
        .trim()
        .charAt(0)
        .toUpperCase();

}


// =====================================================
// ASSIGNMENT HELPERS
// =====================================================

function ensureItemAssignments() {

    bill.items.forEach(item => {

        if (!Array.isArray(item.assigned_to)) {

            item.assigned_to = [];

        }

    });

}


function getAssignedPeople(item) {

    if (
        !item.assigned_to ||
        item.assigned_to.length === 0
    ) {

        return [];

    }

    return people.filter(person =>
        item.assigned_to.includes(person.id)
    );

}


function getAssignmentLabel(item) {

    const assignedPeople =
        getAssignedPeople(item);


    if (assignedPeople.length === 0) {

        return "Assign people";

    }


    if (
        assignedPeople.length ===
        people.length
    ) {

        return "Everyone";

    }


    if (assignedPeople.length === 1) {

        return assignedPeople[0].name;

    }


    if (assignedPeople.length === 2) {

        return assignedPeople
            .map(person => person.name)
            .join(" + ");

    }


    return `${assignedPeople.length} people`;

}


// =====================================================
// RENDER ITEMS
// =====================================================

function renderItems() {

    if (!itemsBody) {
        return;
    }

    ensureItemAssignments();

    itemsBody.innerHTML = "";


    bill.items.forEach((item, index) => {

        const row =
            document.createElement("tr");


        const confidencePercent =
            Math.round(
                (item.confidence ?? 0) * 100
            );


        let confidenceClass =
            "confidence-medium";


        if (confidencePercent >= 85) {

            confidenceClass =
                "confidence-high";

        } else if (confidencePercent < 70) {

            confidenceClass =
                "confidence-low";

        }


        row.innerHTML = `

            <td>

                <input
                    class="edit-input item-name"
                    value="${escapeHtml(item.name)}"
                    data-field="name"
                    data-index="${index}"
                >

            </td>


            <td>

                <input
                    class="edit-input"
                    type="number"
                    min="0.01"
                    step="0.01"
                    value="${item.quantity}"
                    data-field="quantity"
                    data-index="${index}"
                >

            </td>


            <td>

                <input
                    class="edit-input"
                    type="number"
                    min="0"
                    step="0.01"
                    value="${item.unit_price}"
                    data-field="unit_price"
                    data-index="${index}"
                >

            </td>


            <td>

                <strong>
                    ${formatMoney(item.total_price)}
                </strong>

            </td>


            <td>

                <div class="assignment-control">

                    <button
                        type="button"
                        class="assignment-trigger"
                        data-assignment-trigger="${index}"
                    >

                        <span>
                            ${escapeHtml(
                                getAssignmentLabel(item)
                            )}
                        </span>

                        <span>
                            ▾
                        </span>

                    </button>


                    <div
                        class="assignment-menu"
                        data-assignment-menu="${index}"
                        style="display:none;"
                    >

                        <label class="assignment-option">

                            <input
                                type="checkbox"
                                data-everyone="${index}"
                            >

                            <span>
                                Everyone
                            </span>

                        </label>


                        <div
                            style="
                                height:1px;
                                background:#eeeeeb;
                                margin:5px 0;
                            "
                        ></div>


                        ${people.map(person => `

                            <label class="assignment-option">

                                <input
                                    type="checkbox"
                                    class="person-assignment"
                                    data-item="${index}"
                                    data-person="${person.id}"
                                    ${
                                        item.assigned_to.includes(
                                            person.id
                                        )
                                            ? "checked"
                                            : ""
                                    }
                                >

                                <span>
                                    ${escapeHtml(person.name)}
                                </span>

                            </label>

                        `).join("")}

                    </div>

                </div>

            </td>


            <td>

                <span
                    class="confidence-badge ${confidenceClass}"
                >
                    ${confidencePercent}%
                </span>

            </td>


            <td>

                <button
                    class="delete-button"
                    data-delete="${index}"
                    title="Remove item"
                    type="button"
                >
                    ×
                </button>

            </td>

        `;


        itemsBody.appendChild(row);

    });


    if (itemCount) {

        itemCount.textContent =
            `${bill.items.length} items detected`;

    }


    attachInputHandlers();

    attachAssignmentHandlers();

}


// =====================================================
// ITEM INPUT HANDLERS
// =====================================================

function attachInputHandlers() {

    document
        .querySelectorAll(".edit-input")
        .forEach(input => {

            input.addEventListener(
                "input",
                handleEdit
            );

        });


    document
        .querySelectorAll("[data-delete]")
        .forEach(button => {

            button.addEventListener(
                "click",
                deleteItem
            );

        });

}


// =====================================================
// EDIT ITEM
// =====================================================

function handleEdit(event) {

    const input =
        event.target;


    const index =
        Number(input.dataset.index);


    const field =
        input.dataset.field;


    if (!bill.items[index]) {
        return;
    }


    if (field === "name") {

        bill.items[index].name =
            input.value;

    } else {

        bill.items[index][field] =
            Number(input.value) || 0;

    }


    bill.items[index].total_price =
        Number(
            (
                bill.items[index].quantity *
                bill.items[index].unit_price
            ).toFixed(2)
        );


    recalculateBill();

}


// =====================================================
// DELETE ITEM
// =====================================================

function deleteItem(event) {

    const index =
        Number(
            event.currentTarget.dataset.delete
        );


    if (
        Number.isNaN(index) ||
        !bill.items[index]
    ) {

        return;

    }


    const removedItem =
        bill.items[index].name;


    bill.items.splice(index, 1);


    renderItems();

    recalculateBill();


    showToast(
        `${removedItem} removed`
    );

}


// =====================================================
// ADD ITEM
// =====================================================

const addItemButton =
    document.getElementById(
        "addItemButton"
    );


if (addItemButton) {

    addItemButton.addEventListener(
        "click",
        () => {

            bill.items.push({

                name: "New Item",

                quantity: 1,

                unit_price: 0,

                total_price: 0,

                name_confidence: 1,

                quantity_confidence: 1,

                price_confidence: 1,

                confidence: 1,

                assigned_to: people.map(
                    person => person.id
                )

            });


            renderItems();

            recalculateBill();

            showToast(
                "New item added"
            );

        }
    );

}


// =====================================================
// ASSIGNMENT UI
// =====================================================

function attachAssignmentHandlers() {

    document
        .querySelectorAll(
            "[data-assignment-trigger]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                toggleAssignmentMenu
            );

        });


    document
        .querySelectorAll(
            "[data-everyone]"
        )
        .forEach(checkbox => {

            checkbox.addEventListener(
                "change",
                handleEveryoneAssignment
            );

        });


    document
        .querySelectorAll(
            ".person-assignment"
        )
        .forEach(checkbox => {

            checkbox.addEventListener(
                "change",
                handlePersonAssignment
            );

        });

}


// =====================================================
// TOGGLE ASSIGNMENT MENU
// =====================================================

function toggleAssignmentMenu(event) {

    const index =
        Number(
            event.currentTarget.dataset
                .assignmentTrigger
        );


    const menu =
        document.querySelector(
            `[data-assignment-menu="${index}"]`
        );


    if (!menu) {
        return;
    }


    document
        .querySelectorAll(".assignment-menu")
        .forEach(otherMenu => {

            if (otherMenu !== menu) {

                otherMenu.style.display =
                    "none";

            }

        });


    menu.style.display =
        menu.style.display === "none"
            ? "block"
            : "none";


    updateEveryoneCheckbox(index);

}


// =====================================================
// EVERYONE
// =====================================================

function handleEveryoneAssignment(event) {

    const index =
        Number(
            event.target.dataset.everyone
        );


    if (!bill.items[index]) {
        return;
    }


    if (event.target.checked) {

        bill.items[index].assigned_to =
            people.map(
                person => person.id
            );

    } else {

        bill.items[index].assigned_to = [];

    }


    renderItems();

    showToast(
        event.target.checked
            ? "Item assigned to everyone"
            : "Assignment cleared"
    );

}


// =====================================================
// INDIVIDUAL PERSON ASSIGNMENT
// =====================================================

function handlePersonAssignment(event) {

    const index =
        Number(
            event.target.dataset.item
        );


    const personId =
        event.target.dataset.person;


    if (!bill.items[index]) {
        return;
    }


    if (
        !Array.isArray(
            bill.items[index].assigned_to
        )
    ) {

        bill.items[index].assigned_to = [];

    }


    if (event.target.checked) {

        if (
            !bill.items[index]
                .assigned_to
                .includes(personId)
        ) {

            bill.items[index]
                .assigned_to
                .push(personId);

        }

    } else {

        bill.items[index].assigned_to =
            bill.items[index]
                .assigned_to
                .filter(
                    id => id !== personId
                );

    }


    updateAssignmentTrigger(index);

    updateEveryoneCheckbox(index);


    showToast(
        "Assignment updated"
    );

}


// =====================================================
// UPDATE EVERYONE CHECKBOX
// =====================================================

function updateEveryoneCheckbox(index) {

    const checkbox =
        document.querySelector(
            `[data-everyone="${index}"]`
        );


    if (!checkbox || !bill.items[index]) {
        return;
    }


    const assigned =
        bill.items[index].assigned_to || [];


    checkbox.checked =
        people.length > 0 &&
        assigned.length === people.length;

}


// =====================================================
// UPDATE ASSIGNMENT LABEL
// =====================================================

function updateAssignmentTrigger(index) {

    const button =
        document.querySelector(
            `[data-assignment-trigger="${index}"]`
        );


    if (!button || !bill.items[index]) {
        return;
    }


    const span =
        button.querySelector("span");


    if (!span) {
        return;
    }


    span.textContent =
        getAssignmentLabel(
            bill.items[index]
        );

}


// =====================================================
// CLOSE ASSIGNMENT MENUS
// =====================================================

document.addEventListener(
    "click",
    event => {

        if (
            event.target.closest(
                ".assignment-control"
            )
        ) {

            return;

        }


        document
            .querySelectorAll(
                ".assignment-menu"
            )
            .forEach(menu => {

                menu.style.display =
                    "none";

            });

    }
);


// =====================================================
// RECALCULATE BILL
// =====================================================

function recalculateBill() {

    bill.subtotal =
        Number(
            bill.items
                .reduce(
                    (sum, item) =>
                        sum +
                        Number(
                            item.total_price || 0
                        ),
                    0
                )
                .toFixed(2)
        );


    bill.total =
        Number(
            (
                bill.subtotal +
                Number(bill.tax || 0) +
                Number(bill.service_charge || 0) -
                Number(bill.discount || 0)
            ).toFixed(2)
        );


    if (subtotalElement) {

        subtotalElement.textContent =
            formatMoney(
                bill.subtotal
            );

    }


    if (totalElement) {

        totalElement.textContent =
            formatMoney(
                bill.total
            );

    }


    const taxElement =
        document.getElementById("tax");


    if (taxElement) {

        taxElement.textContent =
            formatMoney(
                bill.tax
            );

    }


    const serviceChargeElement =
        document.getElementById(
            "serviceCharge"
        );


    if (serviceChargeElement) {

        serviceChargeElement.textContent =
            formatMoney(
                bill.service_charge
            );

    }


    const discountElement =
        document.getElementById(
            "discount"
        );


    if (discountElement) {

        discountElement.textContent =
            `-${formatMoney(
                bill.discount
            )}`;

    }

}


// =====================================================
// CONFIDENCE
// =====================================================

function updateConfidence() {

    if (
        bill.confidence === undefined ||
        bill.confidence === null
    ) {

        return;

    }


    const confidence =
        Math.round(
            bill.confidence * 100
        );


    if (overallConfidence) {

        overallConfidence.textContent =
            `${confidence}%`;

    }


    const confidenceDot =
        document.querySelector(
            ".confidence-dot"
        );


    if (!confidenceDot) {
        return;
    }


    if (confidence < 70) {

        confidenceDot.style.background =
            "#e14d64";

    } else if (confidence < 85) {

        confidenceDot.style.background =
            "#d88a13";

    } else {

        confidenceDot.style.background =
            "#17a673";

    }

}


// =====================================================
// RECALCULATE BUTTON
// =====================================================

const recalculateButton =
    document.getElementById(
        "recalculateButton"
    );


if (recalculateButton) {

    recalculateButton.addEventListener(
        "click",
        () => {

            recalculateBill();

            renderItems();

            updateConfidence();

            showToast(
                "Bill recalculated"
            );

        }
    );

}


// =====================================================
// VALIDATE BILL
// =====================================================

const validateButton =
    document.getElementById(
        "validateButton"
    );


if (validateButton) {

    validateButton.addEventListener(
        "click",
        async () => {

            try {

                recalculateBill();


                const response =
                    await fetch(
                        "/review",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify(
                                    bill
                                )
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        result.detail ||
                        "Validation request failed"
                    );

                }


                const validation =
                    result.validation;


                if (validation.valid) {

                    if (validationCard) {

                        validationCard.className =
                            "validation-card valid";

                    }


                    if (validationTitle) {

                        validationTitle.textContent =
                            "Bill looks consistent";

                    }


                    if (validationMessage) {

                        validationMessage.textContent =
                            "All extracted values passed arithmetic validation.";

                    }


                    showToast(
                        "Bill validated successfully ✓"
                    );

                } else {

                    if (validationCard) {

                        validationCard.className =
                            "validation-card warning";

                    }


                    if (validationTitle) {

                        validationTitle.textContent =
                            "Review required";

                    }


                    if (validationMessage) {

                        validationMessage.textContent =
                            validation.errors.join(" ");

                    }


                    showToast(
                        "Bill has a mismatch ⚠"
                    );

                }

            } catch (error) {

                console.error(error);


                showToast(
                    error.message ||
                    "Could not validate bill"
                );

            }

        }
    );

}


// =====================================================
// UPLOAD BILL IMAGE
// =====================================================

const uploadButton =
    document.getElementById(
        "uploadButton"
    );


const billImage =
    document.getElementById(
        "billImage"
    );


if (uploadButton && billImage) {

    uploadButton.addEventListener(
        "click",
        () => {

            billImage.click();

        }
    );


    billImage.addEventListener(
        "change",
        async () => {

            if (
                !billImage.files ||
                billImage.files.length === 0
            ) {

                return;

            }


            const file =
                billImage.files[0];


            const allowedTypes = [
                "image/jpeg",
                "image/png",
                "image/jpg",
                "image/webp"
            ];


            if (
                !allowedTypes.includes(
                    file.type
                )
            ) {

                showToast(
                    "Please upload a JPG, PNG or WEBP image."
                );

                billImage.value = "";

                return;

            }


            uploadButton.textContent =
                "Extracting...";


            uploadButton.disabled =
                true;


            showToast(
                "Reading your bill..."
            );


            const formData =
                new FormData();


            formData.append(
                "file",
                file
            );


            try {

                const response =
                    await fetch(
                        "/extract",
                        {
                            method: "POST",
                            body: formData
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        result.detail ||
                        "Could not extract bill"
                    );

                }


                bill =
                    result.bill;


                ensureItemAssignments();


                renderItems();

                recalculateBill();

                updateConfidence();


                uploadButton.textContent =
                    "Image extracted ✓";


                showToast(
                    "Bill extracted successfully ✓"
                );


            } catch (error) {

                console.error(error);


                uploadButton.textContent =
                    "Choose bill image";


                showToast(
                    error.message ||
                    "Could not read bill"
                );


            } finally {

                uploadButton.disabled =
                    false;

            }

        }
    );

}


// =====================================================
// PEOPLE
// =====================================================

function renderPeople() {

    const peopleList =
        document.getElementById(
            "peopleList"
        );


    if (!peopleList) {
        return;
    }


    peopleList.innerHTML = "";


    people.forEach(person => {

        const personElement =
            document.createElement(
                "div"
            );


        personElement.className =
            "person";


        personElement.dataset.personId =
            person.id;


        personElement.innerHTML = `

            <div class="person-avatar">

                ${escapeHtml(
                    getInitial(
                        person.name
                    )
                )}

            </div>


            <span class="person-name">

                ${escapeHtml(
                    person.name
                )}

            </span>


            <button
                class="remove-person-button"
                type="button"
                data-person-id="${person.id}"
                title="Remove member"
                aria-label="Remove ${escapeHtml(
                    person.name
                )}"
            >

                ×

            </button>

        `;


        peopleList.appendChild(
            personElement
        );

    });


    attachPersonHandlers();

    renderItems();

}


// =====================================================
// MEMBER HANDLERS
// =====================================================

function attachPersonHandlers() {

    document
        .querySelectorAll(
            ".remove-person-button"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                removePerson
            );

        });

}


// =====================================================
// REMOVE MEMBER
// =====================================================

function removePerson(event) {

    const personId =
        event.currentTarget.dataset.personId;


    const person =
        people.find(
            item =>
                item.id === personId
        );


    if (!person) {
        return;
    }


    if (people.length === 1) {

        showToast(
            "At least one member is required"
        );

        return;

    }


    people =
        people.filter(
            item =>
                item.id !== personId
        );


    // Remove deleted person from
    // every item's assignments.

    bill.items.forEach(item => {

        if (
            Array.isArray(
                item.assigned_to
            )
        ) {

            item.assigned_to =
                item.assigned_to.filter(
                    id => id !== personId
                );

        }

    });


    renderPeople();


    showToast(
        `${person.name} removed`
    );

}


// =====================================================
// ADD MEMBER
// =====================================================

const addPersonButton =
    document.getElementById(
        "addPersonButton"
    );


if (addPersonButton) {

    addPersonButton.addEventListener(
        "click",
        () => {

            const newPerson = {

                id:
                    `person-${Date.now()}`,

                name:
                    `Person ${people.length + 1}`

            };


            people.push(
                newPerson
            );


            renderPeople();


            showToast(
                "Member added"
            );

        }
    );

}


// =====================================================
// SPLIT BUTTON
// =====================================================

const splitButton =
    document.getElementById(
        "splitButton"
    );


if (splitButton) {

    splitButton.addEventListener(
        "click",
        () => {

            const unassignedItems =
                bill.items.filter(
                    item =>
                        !item.assigned_to ||
                        item.assigned_to.length === 0
                );


            if (
                unassignedItems.length > 0
            ) {

                showToast(
                    "Assign every item before splitting."
                );

                return;

            }


            showToast(
                "Assignments ready ✓"
            );

        }
    );

}


// =====================================================
// INITIALIZE
// =====================================================

ensureItemAssignments();

renderItems();

recalculateBill();

updateConfidence();

renderPeople();