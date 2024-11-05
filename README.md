# INF113 Obligatorisk Innlevering 3 - Eget filsystem i Python

## Hvordan levere oppgaven?
Lever 1 fil for hver av oppgavene, også deloppgavene i oppgave 4. Alt leveres på codegrade.
Oppgavene er progresjonsbasert. Det betyr at du må bruke filen du fikk fra oppgave 1 og fortsette med den i oppgave 2. Det mest praktiske er kanskje å lage en kopi av oppgave 1 når du er ferdig og så jobbe med oppgave 2 fra den. Og så videre.

## Utlevert kode

I denne oppgaven får dere utlevert kode som simulerer et enkelt filsystem. Kjør ´``main.py`` for å generere filsystemet med noen eksempelfiler.

Filsystemet er som helhet lagret i en fil ``myfilesystem.fs`` og er delt inn i blokker. Den første blokken har headerinformasjon om filsystemet, og resten er blokker brukt til filinnhold. Les kommentarer og dokumentasjon i koden for å forstå koden bedre. Det er også mulig å åpne filsystemet som rå data ved å bruke kommando ``xxd myfilesystem.fs`` i terminal. Da vil du se en oversikt over filsystemet i hexadesimalt format.

I ``main.py`` er det lagt til noen tester du kan kjøre etter hver oppgave for å sjekke om koden din fungerer som forventet.

**OBS: Behold så mye av den originale strukturen som mulig, altså ikke slett eller endre funksjoner og funksjonsnavn. Når du jobber med oppgaven må du også tenke over effekten av endringene dine på funksjonaliteten til filsystemet som helhet. For eksempel kan å endre en funksjon ha virkninger for en annen.**

## Oppgave 1: Bedre bruk av frie blokker

#### lever fil: ``myfs_1.py``

Forsøk å forstå hvordan ``save()`` bestemmer hvor en ny fil skal lagres. Tenk over hvorfor dette ikke er ideelt med tanke på at filer kan slettes. Endre koden slik at den alltid finner den første tilgjengelige blokken å skrive til. Dette bør fungere i samspill med ``remove()``, som sletter filer. Pass på at du fortsatt får samme feilmelding dersom du ikke har plass til å lagre flere filer. I tillegg skal det ikke tillates å lagre en tom fil, og du skal bruke feilmeldingen `EmptyFile` når dette er tilfellet.

## Oppgave 2: Bedre lasting av filer

#### lever fil: ``myfs_2.py``

Slik load() er implementert, hva skjer med filer som har gyldige ``\0`` bytes på slutten av innholdet? Vi ønsker å endre load() slik at den leser så mange bytes som filen faktisk inneholder, og ikke hele blokken. Da løser vi det problemet.

Dette vil kreve at vi lagrer filstørrelsen i filens header. Tenk over hvor mye av en file entry du har behov for å bruke til dette formålet, og oppdater ``FILENAME_SIZE`` i henhold til dette. Etter det kan du endre ``save()`` slik at den lagrer filstørrelsen i headeren, og endre ``load()`` slik at den leser riktig antall bytes fra blokken.

Endre også `find_fileno()` slik at den funker med den nye endringen. 

Til slutt, siden vi nå lagrer filstørrelser, kan vi lage en hjelpefunksjon `find_filesize(f, fileno)` som tar filnummeret returnert av `find_fileno()` og returnerer størrelsen til filen som tilhører filnummeret.

## Oppgave 3: Bedre remove()

#### lever fil: ``myfs_3.py``

Siden `load()` nå leser bare eksakt det innholdet som er lagret i en fil og ikke hele blokken, kan vi endre ``remove()`` slik at den gjør mindre arbeid for å frigjøre plass. Din oppgave er å gjøre den endringen. 

## Oppgave 4: hard_link()


Vi har gitt filsystemet en hel blokk til headerinformasjon. Der lagres filnavnene og størrelsene på filene. Men vi har ikke nok blokker til å fylle den fullstendig med file entries. Med den resterende plassen skal vi tillate å lage hard links til eksisterende filer. Altså, en hard link skal kun plasseres som en entry under maks antall filer i headeren.

### Del A

#### lever fil: ``myfs_4A.py``

Implementer ``hard_link(f, existing_file, linked_file)``. Funksjonen skal lage en ny file entry som peker til en eksisterende fil. Med andre ord, funksjonen skal lage en hard link. 

Som var del av den utleverte koden, har filsystemet en teller for å holde styr på hvor mange filer som filsystemet har. Du skal nå bruke den neste tilgjengelige plassen i systemets header til å telle hvor mange hard links som filsystemet har. Det er dette `_get_num_linked_files` og `_set_num_linked_files` skal brukes til, så implementer disse funksjonene.

Oppdater også `load()` slik at den kan lese innholdet fra en hard link. Du må kanskje også oppdatere `find_fileno()` igjen avhengig av hvordan du har implementert resten av oppgaven. 

(Hint: Filstørrelsen er ikke nødvendig for en hard link siden den eksisterende filen allerede har den. Du kan bruke denne plassen til noe annet for å implementere hard_link.)

### Del B

#### lever fil: ``myfs_4B.py``
Oppdater `remove()` slik: 
- Hvis `remove()` blir kallet for en fil, skal filens originale file entry erstattes av den øverste hard linken som peker til filen. Hvis det ikke finnes noen slike hard linker, skal filen slettes.
- Hvis `remove()` blir kallet for en hard link, skal hard linken slettes. 
- Husk å bruke `NoFile` som exception når filnavnet ikke finnes hverken som fil eller link.