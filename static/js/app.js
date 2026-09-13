// =====================================================
// SPLITBILL FRONTEND
// =====================================================


// =====================================================
// DOM ELEMENTS
// =====================================================

const uploadModeButton =
    document.getElementById("uploadModeButton");

const manualModeButton =
    document.getElementById("manualModeButton");

const photoEntryPanel =
    document.getElementById("photoEntryPanel");

const manualEntryPanel =
    document.getElementById("manualEntryPanel");

const uploadButton =
    document.getElementById("uploadButton");

const billImage =
    document.getElementById("billImage");

const fileStatus =
    document.getElementById("fileStatus");

const itemsBody =
    document.getElementById("itemsBody");

const itemCount =
    document.getElementById("itemCount");

const subtotalElement =
    document.getElementById("subtotal");

const taxElement =
    document.getElementById("tax");

const serviceChargeElement =
    document.getElementById("serviceCharge");

const discountElement =
    document.getElementById("discount");

const totalElement =
    document.getElementById("total");

const validationCard =
    document.getElementById("validationCard");

const validationTitle =
    document.getElementById("validationTitle");

const validationMessage =
    document.getElementById("validationMessage");

const overallConfidence =
    document.getElementById("overallConfidence");

const toast =
    document.getElementById("toast");


// =====================================================
// BILL STATE
// =====================================================

let bill = {

    items: [],

    subtotal: 0,

    tax: 0,

    service_charge: 0,

    discount: 0,

    total: 0,

    subtotal_confidence: 0,

    tax_confidence: 0,

    service_charge_confidence: 0,

    discount_confidence: 0,

    total_confidence: 0,

    confidence: 0

};


// =====================================================
// PEOPLE
// =====================================================

let people = [];


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

    }, 2200);

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

    return String(name || "")
        .trim()
        .charAt(0)
        .toUpperCase();

}


// =====================================================
// MODE SWITCH
// =====================================================

function setEntryMode(mode) {

    if (mode === "manual") {

        manualModeButton?.classList.add("active");

        uploadModeButton?.classList.remove("active");

        manualEntryPanel?.classList.remove("hidden");

        photoEntryPanel?.classList.add("hidden");

    } else {

        uploadModeButton?.classList.add("active");

        manualModeButton?.classList.remove("active");

        photoEntryPanel?.classList.remove("hidden");

        manualEntryPanel?.classList.add("hidden");

    }

}


uploadModeButton?.addEventListener(
    "click",
    () => {

        setEntryMode("photo");

    }
);


manualModeButton?.addEventListener(
    "click",
    () => {

        setEntryMode("manual");

        initializeManualBill();

    }
);


// =====================================================
// PHOTO UPLOAD
// =====================================================

uploadButton?.addEventListener(
    "click",
    () => {

        billImage?.click();

    }
);


billImage?.addEventListener(
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


        fileStatus.textContent =
            file.name;


        uploadButton.disabled =
            true;


        uploadButton.textContent =
            "Extracting...";


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
                    "Could not extract bill."
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


            document
                .getElementById("reviewSection")
                ?.scrollIntoView({
                    behavior: "smooth"
                });


        } catch (error) {

            console.error(error);


            showToast(
                error.message ||
                "Could not read bill."
            );


            uploadButton.textContent =
                "↑ Choose bill image";


        } finally {

            uploadButton.disabled =
                false;

        }

    }
);


// =====================================================
// MANUAL BILL
// =====================================================

let manualBillInitialized =
    false;


function initializeManualBill() {

    if (manualBillInitialized) {

        return;

    }


    manualBillInitialized =
        true;


    addManualItem();


    document
        .getElementById("manualAddItem")
        ?.addEventListener(
            "click",
            addManualItem
        );


    document
        .getElementById("manualTaxEnabled")
        ?.addEventListener(
            "change",
            toggleManualTax
        );


    document
        .getElementById("manualServiceEnabled")
        ?.addEventListener(
            "change",
            toggleManualService
        );


    document
        .getElementById("manualTax")
        ?.addEventListener(
            "input",
            calculateManualBill
        );


    document
        .getElementById("manualService")
        ?.addEventListener(
            "input",
            calculateManualBill
        );


    document
        .getElementById("manualDiscount")
        ?.addEventListener(
            "input",
            calculateManualBill
        );


    document
        .getElementById("manualContinue")
        ?.addEventListener(
            "click",
            continueManualBill
        );


    calculateManualBill();

}


function toggleManualTax(event) {

    const input =
        document.getElementById(
            "manualTax"
        );


    if (input) {

        input.disabled =
            !event.target.checked;

    }


    calculateManualBill();

}


function toggleManualService(event) {

    const input =
        document.getElementById(
            "manualService"
        );


    if (input) {

        input.disabled =
            !event.target.checked;

    }


    calculateManualBill();

}


// =====================================================
// ADD MANUAL ITEM
// =====================================================

function addManualItem() {

    const container =
        document.getElementById(
            "manualItems"
        );


    if (!container) {

        return;

    }


    const row =
        document.createElement(
            "div"
        );


    row.className =
        "manual-item-row";


    row.innerHTML = `

        <input
            type="text"
            class="manual-item-name"
            placeholder="Item name"
        >

        <input
            type="number"
            class="manual-item-qty"
            min="0.01"
            step="0.01"
            value="1"
            placeholder="Qty"
        >

        <input
            type="number"
            class="manual-item-price"
            min="0"
            step="0.01"
            value="0"
            placeholder="Unit price"
        >

        <strong
            class="manual-item-total"
        >
            ₹0.00
        </strong>

        <button
            type="button"
            class="manual-remove"
            title="Remove item"
        >
            ×
        </button>

    `;


    container.appendChild(row);


    row
        .querySelectorAll("input")
        .forEach(input => {

            input.addEventListener(
                "input",
                calculateManualBill
            );

        });


    row
        .querySelector(
            ".manual-remove"
        )
        .addEventListener(
            "click",
            () => {

                row.remove();

                calculateManualBill();

            }
        );


    row
        .querySelector(
            ".manual-item-name"
        )
        ?.focus();


    calculateManualBill();

}


// =====================================================
// CALCULATE MANUAL BILL
// =====================================================

function calculateManualBill() {

    const rows =
        document.querySelectorAll(
            ".manual-item-row"
        );


    let subtotal = 0;


    rows.forEach(row => {

        const quantity =
            Number(
                row.querySelector(
                    ".manual-item-qty"
                )?.value || 0
            );


        const price =
            Number(
                row.querySelector(
                    ".manual-item-price"
                )?.value || 0
            );


        const itemTotal =
            Number(
                (
                    quantity *
                    price
                ).toFixed(2)
            );


        subtotal +=
            itemTotal;


        const totalElement =
            row.querySelector(
                ".manual-item-total"
            );


        if (totalElement) {

            totalElement.textContent =
                formatMoney(itemTotal);

        }

    });


    subtotal =
        Number(
            subtotal.toFixed(2)
        );


    const taxEnabled =
        document.getElementById(
            "manualTaxEnabled"
        )?.checked || false;


    const serviceEnabled =
        document.getElementById(
            "manualServiceEnabled"
        )?.checked || false;


    const tax =
        taxEnabled
            ? Number(
                document.getElementById(
                    "manualTax"
                )?.value || 0
            )
            : 0;


    const service =
        serviceEnabled
            ? Number(
                document.getElementById(
                    "manualService"
                )?.value || 0
            )
            : 0;


    const discount =
        Number(
            document.getElementById(
                "manualDiscount"
            )?.value || 0
        );


    const total =
        Number(
            (
                subtotal +
                tax +
                service -
                discount
            ).toFixed(2)
        );


    document.getElementById(
        "manualSubtotal"
    ).textContent =
        formatMoney(subtotal);


    document.getElementById(
        "manualTaxSummary"
    ).textContent =
        formatMoney(tax);


    document.getElementById(
        "manualServiceSummary"
    ).textContent =
        formatMoney(service);


    document.getElementById(
        "manualDiscountSummary"
    ).textContent =
        `-${formatMoney(discount)}`;


    document.getElementById(
        "manualTotal"
    ).textContent =
        formatMoney(total);


    return {

        subtotal,
        tax,
        service,
        discount,
        total

    };

}


// =====================================================
// CONTINUE MANUAL BILL
// =====================================================

function continueManualBill() {

    const rows =
        document.querySelectorAll(
            ".manual-item-row"
        );


    const items = [];


    rows.forEach(row => {

        const name =
            row.querySelector(
                ".manual-item-name"
            )?.value.trim();


        const quantity =
            Number(
                row.querySelector(
                    ".manual-item-qty"
                )?.value || 0
            );


        const unitPrice =
            Number(
                row.querySelector(
                    ".manual-item-price"
                )?.value || 0
            );


        if (
            name &&
            quantity > 0 &&
            unitPrice >= 0
        ) {

            items.push({

                name,

                quantity,

                unit_price:
                    unitPrice,

                total_price:
                    Number(
                        (
                            quantity *
                            unitPrice
                        ).toFixed(2)
                    ),

                name_confidence: 1,

                quantity_confidence: 1,

                price_confidence: 1,

                confidence: 1,

                assigned_to: []

            });

        }

    });


    if (items.length === 0) {

        showToast(
            "Please add at least one valid item."
        );

        return;

    }


    const calculated =
        calculateManualBill();


    bill = {

        items,

        subtotal:
            calculated.subtotal,

        tax:
            calculated.tax,

        service_charge:
            calculated.service,

        discount:
            calculated.discount,

        total:
            calculated.total,

        subtotal_confidence: 1,

        tax_confidence: 1,

        service_charge_confidence: 1,

        discount_confidence: 1,

        total_confidence: 1,

        confidence: 1

    };


    ensureItemAssignments();

    renderItems();

    recalculateBill();

    updateConfidence();


    document
        .getElementById(
            "reviewSection"
        )
        ?.scrollIntoView({
            behavior: "smooth"
        });


    showToast(
        "Manual bill created successfully ✓"
    );

}


// =====================================================
// ASSIGNMENT
// =====================================================

function ensureItemAssignments() {

    bill.items.forEach(item => {

        if (
            !Array.isArray(
                item.assigned_to
            )
        ) {

            item.assigned_to = [];

        }

    });

}


function getAssignedPeople(item) {

    return people.filter(
        person =>
            item.assigned_to.includes(
                person.id
            )
    );

}


function getAssignmentLabel(item) {

    const assigned =
        getAssignedPeople(item);


    if (assigned.length === 0) {

        return "Assign people";

    }


    if (
        assigned.length ===
        people.length
    ) {

        return "Everyone";

    }


    if (assigned.length === 1) {

        return assigned[0].name;

    }


    if (assigned.length === 2) {

        return assigned
            .map(person => person.name)
            .join(" + ");

    }


    return `${assigned.length} people`;

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


    bill.items.forEach(
        (item, index) => {

            const row =
                document.createElement(
                    "tr"
                );


            const confidence =
                Math.round(
                    Number(
                        item.confidence || 0
                    ) * 100
                );


            let confidenceClass =
                "confidence-medium";


            if (confidence >= 85) {

                confidenceClass =
                    "confidence-high";

            } else if (
                confidence < 70
            ) {

                confidenceClass =
                    "confidence-low";

            }


            row.innerHTML = `

                <td>

                    <input
                        class="edit-input"
                        data-index="${index}"
                        data-field="name"
                        value="${escapeHtml(item.name)}"
                    >

                </td>


                <td>

                    <input
                        class="edit-input"
                        type="number"
                        min="0.01"
                        step="0.01"
                        data-index="${index}"
                        data-field="quantity"
                        value="${item.quantity}"
                    >

                </td>


                <td>

                    <input
                        class="edit-input"
                        type="number"
                        min="0"
                        step="0.01"
                        data-index="${index}"
                        data-field="unit_price"
                        value="${item.unit_price}"
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
                                    ${
                                        people.length > 0 &&
                                        item.assigned_to.length === people.length
                                            ? "checked"
                                            : ""
                                    }
                                >

                                <span>
                                    Everyone
                                </span>

                            </label>


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
                        ${confidence}%
                    </span>

                </td>


                <td>

                    <button
                        type="button"
                        class="delete-button"
                        data-delete="${index}"
                    >
                        ×
                    </button>

                </td>

            `;


            itemsBody.appendChild(row);

        }
    );


    if (itemCount) {

        itemCount.textContent =
            `${bill.items.length} items`;

    }


    attachItemHandlers();

}


// =====================================================
// ITEM HANDLERS
// =====================================================

function attachItemHandlers() {

    document
        .querySelectorAll(
            ".edit-input"
        )
        .forEach(input => {

            input.addEventListener(
                "input",
                handleItemEdit
            );

        });


    document
        .querySelectorAll(
            "[data-delete]"
        )
        .forEach(button => {

            button.addEventListener(
                "click",
                deleteItem
            );

        });


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
// EDIT ITEM
// =====================================================

function handleItemEdit(event) {

    const input =
        event.target;


    const index =
        Number(
            input.dataset.index
        );


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

    refreshItemTotalOnly(
        index
    );

}


function refreshItemTotalOnly(index) {

    const rows =
        itemsBody.querySelectorAll(
            "tr"
        );


    const row =
        rows[index];


    if (!row) {

        return;

    }


    const total =
        row.querySelector(
            "td:nth-child(4) strong"
        );


    if (total) {

        total.textContent =
            formatMoney(
                bill.items[index].total_price
            );

    }

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


    const name =
        bill.items[index].name;


    bill.items.splice(
        index,
        1
    );


    renderItems();

    recalculateBill();


    showToast(
        `${name} removed`
    );

}


// =====================================================
// ADD REVIEW ITEM
// =====================================================

document
    .getElementById(
        "addItemButton"
    )
    ?.addEventListener(
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

                assigned_to: []

            });


            renderItems();

            recalculateBill();


            showToast(
                "New item added"
            );

        }
    );


// =====================================================
// ASSIGNMENT MENU
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
        .querySelectorAll(
            ".assignment-menu"
        )
        .forEach(other => {

            if (other !== menu) {

                other.style.display =
                    "none";

            }

        });


    menu.style.display =
        menu.style.display === "none"
            ? "block"
            : "none";

}


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

        bill.items[index].assigned_to =
            [];

    }


    renderItems();


    showToast(
        event.target.checked
            ? "Item assigned to everyone"
            : "Assignment cleared"
    );

}


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

        bill.items[index].assigned_to =
            [];

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

        bill.items[index]
            .assigned_to =
            bill.items[index]
                .assigned_to
                .filter(
                    id =>
                        id !== personId
                );

    }


    updateAssignmentLabel(
        index
    );

}


function updateAssignmentLabel(index) {

    const button =
        document.querySelector(
            `[data-assignment-trigger="${index}"]`
        );


    if (!button) {

        return;

    }


    const span =
        button.querySelector(
            "span"
        );


    if (span) {

        span.textContent =
            getAssignmentLabel(
                bill.items[index]
            );

    }

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
// ADD MEMBER
// =====================================================

document
    .getElementById(
        "addPersonButton"
    )
    ?.addEventListener(
        "click",
        addMember
    );


document
    .getElementById(
        "memberNameInput"
    )
    ?.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Enter"
            ) {

                addMember();

            }

        }
    );


function addMember() {

    const input =
        document.getElementById(
            "memberNameInput"
        );


    const name =
        input?.value.trim();


    if (!name) {

        showToast(
            "Enter a member name first."
        );

        input?.focus();

        return;

    }


    const duplicate =
        people.some(
            person =>
                person.name.toLowerCase() ===
                name.toLowerCase()
        );


    if (duplicate) {

        showToast(
            "This member already exists."
        );

        input?.focus();

        return;

    }


    const person = {

        id:
            `person-${Date.now()}-${Math.random()
                .toString(16)
                .slice(2)}`,

        name

    };


    people.push(person);


    input.value = "";


    renderPeople();

    renderItems();


    showToast(
        `${name} added ✓`
    );

}


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

        const element =
            document.createElement(
                "div"
            );


        element.className =
            "person";


        element.innerHTML = `

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
                type="button"
                class="remove-person-button"
                data-person-id="${person.id}"
            >
                ×
            </button>

        `;


        element
            .querySelector(
                ".remove-person-button"
            )
            .addEventListener(
                "click",
                () => {

                    removeMember(
                        person.id
                    );

                }
            );


        peopleList.appendChild(
            element
        );

    });

}


function removeMember(personId) {

    const person =
        people.find(
            item =>
                item.id === personId
        );


    if (!person) {

        return;

    }


    people =
        people.filter(
            item =>
                item.id !== personId
        );


    bill.items.forEach(item => {

        item.assigned_to =
            (
                item.assigned_to || []
            ).filter(
                id =>
                    id !== personId
            );

    });


    renderPeople();

    renderItems();


    showToast(
        `${person.name} removed`
    );

}


// =====================================================
// RECALCULATE BILL
// =====================================================

function recalculateBill() {

    bill.items.forEach(item => {

        item.total_price =
            Number(
                (
                    Number(item.quantity || 0) *
                    Number(item.unit_price || 0)
                ).toFixed(2)
            );

    });


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


    if (taxElement) {

        taxElement.textContent =
            formatMoney(
                bill.tax
            );

    }


    if (serviceChargeElement) {

        serviceChargeElement.textContent =
            formatMoney(
                bill.service_charge
            );

    }


    if (discountElement) {

        discountElement.textContent =
            `-${formatMoney(
                bill.discount
            )}`;

    }


    if (totalElement) {

        totalElement.textContent =
            formatMoney(
                bill.total
            );

    }

}


// =====================================================
// CONFIDENCE
// =====================================================

function updateConfidence() {

    const confidence =
        Math.round(
            Number(
                bill.confidence || 0
            ) * 100
        );


    if (overallConfidence) {

        overallConfidence.textContent =
            `${confidence}%`;

    }


    const dot =
        document.querySelector(
            ".confidence-dot"
        );


    if (!dot) {

        return;

    }


    if (confidence < 70) {

        dot.style.background =
            "#b94a48";

    } else if (
        confidence < 85
    ) {

        dot.style.background =
            "#8a7226";

    } else {

        dot.style.background =
            "#287a52";

    }

}


// =====================================================
// RECALCULATE BUTTON
// =====================================================

document
    .getElementById(
        "recalculateButton"
    )
    ?.addEventListener(
        "click",
        () => {

            recalculateBill();

            renderItems();

            updateConfidence();

            showToast(
                "Bill recalculated ✓"
            );

        }
    );


// =====================================================
// VALIDATE BILL
// =====================================================

document
    .getElementById(
        "validateButton"
    )
    ?.addEventListener(
        "click",
        async () => {

            if (
                bill.items.length === 0
            ) {

                showToast(
                    "Add a bill first."
                );

                return;

            }


            recalculateBill();


            try {

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
                        "Validation failed."
                    );

                }


                const validation =
                    result.validation;


                if (
                    validation.valid
                ) {

                    validationCard.className =
                        "validation-card";


                    validationTitle.textContent =
                        "Bill looks consistent";


                    validationMessage.textContent =
                        "All item totals and bill amounts passed arithmetic validation.";


                    showToast(
                        "Bill validated successfully ✓"
                    );

                } else {

                    validationCard.className =
                        "validation-card warning";


                    validationTitle.textContent =
                        "Review required";


                    validationMessage.textContent =
                        validation.errors.join(
                            " "
                        );


                    showToast(
                        "Bill has a mismatch ⚠"
                    );

                }

            } catch (error) {

                console.error(error);


                showToast(
                    error.message ||
                    "Could not validate bill."
                );

            }

        }
    );


// =====================================================
// SPLIT BILL
// =====================================================

document
    .getElementById(
        "splitButton"
    )
    ?.addEventListener(
        "click",
        async () => {

            if (
                bill.items.length === 0
            ) {

                showToast(
                    "Add a bill first."
                );

                return;

            }


            if (
                people.length === 0
            ) {

                showToast(
                    "Add at least one member."
                );

                return;

            }


            const unassigned =
                bill.items.filter(
                    item =>
                        !item.assigned_to ||
                        item.assigned_to.length === 0
                );


            if (
                unassigned.length > 0
            ) {

                showToast(
                    "Assign every item before splitting."
                );

                return;

            }


            const splitButton =
                document.getElementById(
                    "splitButton"
                );


            splitButton.disabled =
                true;


            splitButton.textContent =
                "Calculating...";


            try {

                recalculateBill();


                const response =
                    await fetch(
                        "/split",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body:
                                JSON.stringify({
                                    bill,
                                    people
                                })
                        }
                    );


                const result =
                    await response.json();


                if (!response.ok) {

                    throw new Error(
                        result.detail ||
                        "Could not split the bill."
                    );

                }


                renderSplitResults(
                    result
                );


                showToast(
                    "Bill split successfully ✓"
                );

            } catch (error) {

                console.error(error);


                showToast(
                    error.message ||
                    "Could not calculate split."
                );

            } finally {

                splitButton.disabled =
                    false;

                splitButton.textContent =
                    "Split bill →";

            }

        }
    );


// =====================================================
// SPLIT RESULTS
// =====================================================

function renderSplitResults(data) {

    const container =
        document.getElementById(
            "splitResults"
        );


    if (!container) {

        return;

    }


    const results =
        data.results || [];


    container.classList.remove(
        "hidden"
    );


    container.innerHTML = `

        <div class="results-heading">

            <div>

                <span class="mini-label">
                    STEP 04 · FINAL SPLIT
                </span>

                <h2>
                    Everyone's share
                </h2>

                <p>
                    Tax and service charge are allocated
                    according to actual consumption.
                </p>

            </div>


            <div class="results-total">

                <span>
                    BILL TOTAL
                </span>

                <strong>
                    ${formatMoney(
                        data.total
                    )}
                </strong>

            </div>

        </div>


        <div class="results-grid">

            ${results.map(result => `

                <article class="result-card">

                    <div class="result-header">

                        <div class="result-avatar">

                            ${escapeHtml(
                                getInitial(
                                    result.person_name
                                )
                            )}

                        </div>

                        <div>

                            <strong>
                                ${escapeHtml(
                                    result.person_name
                                )}
                            </strong>

                            <span>
                                Final amount
                            </span>

                        </div>

                    </div>


                    <div class="result-breakdown">

                        <div>

                            <span>
                                Items consumed
                            </span>

                            <strong>
                                ${formatMoney(
                                    result.item_total
                                )}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Tax
                            </span>

                            <strong>
                                ${formatMoney(
                                    result.tax
                                )}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Service charge
                            </span>

                            <strong>
                                ${formatMoney(
                                    result.service_charge
                                )}
                            </strong>

                        </div>


                        <div>

                            <span>
                                Discount
                            </span>

                            <strong>
                                -${formatMoney(
                                    result.discount
                                )}
                            </strong>

                        </div>

                    </div>


                    <div class="result-final">

                        <span>
                            YOU PAY
                        </span>

                        <strong>
                            ${formatMoney(
                                result.final_total
                            )}
                        </strong>

                    </div>

                </article>

            `).join("")}

        </div>

    `;


    container.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// =====================================================
// INITIALIZE
// =====================================================

renderPeople();

renderItems();

recalculateBill();

updateConfidence();

setEntryMode("photo");