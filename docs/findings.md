**This contains: the main findings and differences between the `localisations_1_2_0.plist`, which is the the file of source of truth and the `localisations_1_2_1.plist` which is the supposed update to the localisations AND how I'd propose the team uses a tool like this**

For my current understanding the `localisations_1_2_0.plist` file has 3 main keys which contain many different map language code and respective strings. The first key has 8 basic languages which are American English, French, Italian, German, Spanish, Brazilian Portuguese, Russian, and Turkish. And the second and third keys follow the same list of languages as the first, sometimes changing their respective sequence order. Since it is the source of truth, I will assume for now that is correct; there are no empty strings, all of the '\n' seem well formatted in the first and last key of this file.

There is only 1 thing to point which is the use of `%u` in the second key which alerts for the `%@` problem described in the specifications; on the line 33 there seems to be a missing character to the `%` therefore being a huge error that has to be fixed in `localisations_1_2_1.plist`. 


For this second file `localisations_1_2_1.plist` there are a lot of changes. This update removes one of the localisations for the "Play as Guest key" and adds 2 new localisations keys with as similar language structure and the previous keys. The main changes I detected so far are:

- the change in the sequence order of the old keys and their respective languages, which is not exactly an error but a change nonetheless;
- the `2b827952-8d1a-4c31-9283-8753d1fc51be` key was updated: 
  - it fixed the `%u` error in the french language entry; 
  - the Italian language entry has an empty string error; 
  - the Russian language code entry is missing the character 'u' to complete the `%u` so its a big error which must be detected and corrected; 
  - a Japanase language code entry was added but the Spanish language code entry was removed entirely.
- the `d8225439-0a23-404c-857d-8cd37032a606` key was also updated:
  - The Spanish language code entry was removed entirely;
  - A Japanese language code entry was added but it does not have any '\n' element
- as discussed before the `7a794655-44e9-49d6-99c6-df936bec3fcc` key was removed entirely and 2 new keys have been added;
- the `9bb069bc-a70c-45ce-875b-225f8ccef615` key and language code entries have really long translations which could cause overflow, here it would be necessary to trim the text and add more '\n' elements to the text;
- the `981dc5a-a6b8-4fd3-be04-052522e08c86` key also does not have any kind of '\n' elements to properly display the text;
- the 2 new keys also have the newly added Japanese language code entries and removed the Spanish language codes entirely.

Prioritization of errors and ranked by risk:
1. a translation that quietly dropped a full old key;
2. a translation that quietly dropped a %@ placeholder;
3. a key that lost a language it used to have;
4. an empty string;
5. a text that's suddenly longer and overflows the button it lives in.

**How I would propose the team uses this tool**

I would propose using this tool as a permanent safety check in the release process, especially before a localisation file is deployed to production. The most useful place for it would be in the CI/CD pipeline, running automatically when a new localisation plist is added or changed.

For example, during a deploy, the pipeline could compare the current production localisation file against the candidate file:

```bash
poetry run tool verify original_localisations/localisations_1_2_0.plist original_localisations/localisations_1_2_1.plist
